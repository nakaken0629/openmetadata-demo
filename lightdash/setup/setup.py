"""Lightdash の初期セットアップを API で行う。

1. 管理者ユーザーを登録する（ログインできる場合は登録済みとみなして省略）
2. 組織を作成する（作成済みの場合は省略）
3. プロジェクトを作成する（同名のプロジェクトがある場合は省略）
4. プロジェクトをリフレッシュし、dbt プロジェクトのコンパイル完了を待つ

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


def main():
    wait_for_lightdash()
    login_or_register()
    ensure_organization()
    project_uuid = ensure_project()
    refresh_project(project_uuid)
    print("Done")


if __name__ == "__main__":
    main()
