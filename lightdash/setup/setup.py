"""Lightdash の初期セットアップを API で行う。

1. 管理者ユーザーを登録する（ログインできる場合は登録済みとみなして省略）
2. 組織を作成する（作成済みの場合は省略）
3. プロジェクトを作成する（同名のプロジェクトがある場合は省略）
4. プロジェクトをリフレッシュし、dbt プロジェクトのコンパイル完了を待つ
5. スペースと、サンプルのチャート・ダッシュボードを作成する（同名のものがある場合は省略）

何度実行しても同じ状態になる。設定は環境変数で指定する。
"""

import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = os.environ["LIGHTDASH_URL"].rstrip("/") + "/api/v1"
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
ORGANIZATION_NAME = os.environ["ORGANIZATION_NAME"]
PROJECT_NAME = os.environ["PROJECT_NAME"]
SPACE_NAME = os.environ["SPACE_NAME"]
DASHBOARD_NAME = os.environ["DASHBOARD_NAME"]

# サンプルのチャート（名前、Explore、ディメンション、メトリクス）。いずれも棒グラフ
CHARTS = [
    ("月別売上", "fct_orders", "fct_orders_order_date_month", "fct_orders_total_revenue"),
    ("会員ランク別の売上", "fct_orders", "dim_customers_membership_rank", "fct_orders_total_revenue"),
    ("キャンペーン別のコンバージョン率", "fct_sessions", "dim_campaigns_campaign_name", "fct_sessions_conversion_rate"),
    ("問い合わせの種類別件数", "fct_inquiries", "fct_inquiries_category", "fct_inquiries_inquiry_count"),
]

PROJECT = {
    "name": PROJECT_NAME,
    "type": "DEFAULT",
    "dbtVersion": os.environ["DBT_VERSION"],
    "dbtConnection": {"type": "dbt", "project_dir": os.environ["DBT_PROJECT_DIR"]},
    "warehouseConnection": {
        "type": "postgres",
        "host": os.environ["WAREHOUSE_HOST"],
        "port": int(os.environ["WAREHOUSE_PORT"]),
        "user": os.environ["WAREHOUSE_USER"],
        "password": os.environ["WAREHOUSE_PASSWORD"],
        "dbname": os.environ["WAREHOUSE_DBNAME"],
        "schema": os.environ["WAREHOUSE_SCHEMA"],
        "sslmode": "disable",
    },
}

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def request(method, path, body=None):
    """API を呼び出し、(HTTP ステータス, レスポンスの JSON) を返す。"""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE_URL + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with opener.open(req) as res:
            return res.status, json.load(res)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def call(method, path, body=None):
    """API を呼び出し、失敗した場合は終了する。"""
    status, res = request(method, path, body)
    if status >= 400:
        sys.exit(f"{method} {path} failed ({status}): {res.get('error', res)}")
    return res.get("results")


def wait_for_lightdash():
    print("Waiting for Lightdash to become available...")
    for _ in range(120):
        try:
            if request("GET", "/health")[0] == 200:
                return
        except (urllib.error.URLError, ConnectionError):
            pass
        time.sleep(5)
    sys.exit("Lightdash did not become available")


def login_or_register():
    status, _ = request("POST", "/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if status == 200:
        print(f"Logged in as {ADMIN_EMAIL}")
        return
    call("POST", "/user", {"firstName": "Admin", "lastName": "User", "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    print(f"Registered admin user {ADMIN_EMAIL}")


def ensure_organization():
    if call("GET", "/user").get("organizationUuid"):
        print("Organization already exists")
        return
    call("PUT", "/org", {"name": ORGANIZATION_NAME})
    print(f"Created organization '{ORGANIZATION_NAME}'")


def ensure_project():
    for project in call("GET", "/org/projects"):
        if project["name"] == PROJECT_NAME:
            print(f"Project '{PROJECT_NAME}' already exists")
            return project["projectUuid"]
    project_uuid = call("POST", "/org/projects", PROJECT)["project"]["projectUuid"]
    print(f"Created project '{PROJECT_NAME}'")
    return project_uuid


def refresh_project(project_uuid):
    # プロジェクトを作成しただけでは dbt プロジェクトがコンパイルされないため、リフレッシュする
    job_uuid = call("POST", f"/projects/{project_uuid}/refresh")["jobUuid"]
    print("Refreshing dbt project...")
    for _ in range(120):
        status = call("GET", f"/jobs/{job_uuid}")["jobStatus"]
        if status == "DONE":
            explores = call("GET", f"/projects/{project_uuid}/explores")
            errors = [e["name"] for e in explores if e.get("errors")]
            print(f"Compiled {len(explores)} explores" + (f" (errors: {', '.join(errors)})" if errors else ""))
            return
        if status == "ERROR":
            sys.exit("Failed to compile dbt project. See the compile logs in Lightdash.")
        time.sleep(5)
    sys.exit("Timed out waiting for dbt project compilation")


def ensure_space(project_uuid):
    for space in call("GET", f"/projects/{project_uuid}/spaces"):
        if space["name"] == SPACE_NAME:
            print(f"Space '{SPACE_NAME}' already exists")
            return space["uuid"]
    space_uuid = call("POST", f"/projects/{project_uuid}/spaces", {"name": SPACE_NAME})["uuid"]
    print(f"Created space '{SPACE_NAME}'")
    return space_uuid


def ensure_charts(project_uuid, space_uuid):
    existing = {c["name"]: c["uuid"] for c in call("GET", f"/projects/{project_uuid}/charts") if c["spaceUuid"] == space_uuid}
    chart_uuids = []
    for name, explore, dimension, metric in CHARTS:
        if name in existing:
            print(f"Chart '{name}' already exists")
            chart_uuids.append(existing[name])
            continue
        chart = {
            "name": name,
            "tableName": explore,
            "spaceUuid": space_uuid,
            "metricQuery": {
                "exploreName": explore,
                "dimensions": [dimension],
                "metrics": [metric],
                "filters": {},
                "sorts": [{"fieldId": dimension, "descending": False}],
                "limit": 500,
                "tableCalculations": [],
            },
            "chartConfig": {
                "type": "cartesian",
                "config": {
                    "layout": {"xField": dimension, "yField": [metric]},
                    "eChartsConfig": {
                        "series": [{"type": "bar", "encode": {"xRef": {"field": dimension}, "yRef": {"field": metric}}}]
                    },
                },
            },
            "tableConfig": {"columnOrder": []},
        }
        chart_uuids.append(call("POST", f"/projects/{project_uuid}/saved", chart)["uuid"])
        print(f"Created chart '{name}'")
    return chart_uuids


def ensure_dashboard(project_uuid, space_uuid, chart_uuids):
    for dashboard in call("GET", f"/projects/{project_uuid}/dashboards"):
        if dashboard["name"] == DASHBOARD_NAME:
            print(f"Dashboard '{DASHBOARD_NAME}' already exists")
            return
    # チャートを 2 列に並べる
    tiles = [
        {
            "type": "saved_chart",
            "x": (i % 2) * 18,
            "y": (i // 2) * 9,
            "w": 18,
            "h": 9,
            "properties": {"savedChartUuid": chart_uuid},
        }
        for i, chart_uuid in enumerate(chart_uuids)
    ]
    call("POST", f"/projects/{project_uuid}/dashboards", {"name": DASHBOARD_NAME, "spaceUuid": space_uuid, "tiles": tiles, "tabs": []})
    print(f"Created dashboard '{DASHBOARD_NAME}'")


def main():
    wait_for_lightdash()
    login_or_register()
    ensure_organization()
    project_uuid = ensure_project()
    refresh_project(project_uuid)
    space_uuid = ensure_space(project_uuid)
    chart_uuids = ensure_charts(project_uuid, space_uuid)
    ensure_dashboard(project_uuid, space_uuid, chart_uuids)
    # OpenMetadata で Lightdash のサービスを作成する際に入力する値
    print(f"Project UUID: {project_uuid}")
    print(f"Space UUID: {space_uuid}")
    print("Done")


if __name__ == "__main__":
    main()
