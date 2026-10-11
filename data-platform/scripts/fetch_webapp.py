"""Web アプリのエクスポートファイルを用意する。

dbt-labs/jaffle_shop（Apache License 2.0）の seeds を、ファイル名を変更して sources/webapp/ に保存する。
取得元はコミットを固定しているため、常に同じファイルが取得される。すでにファイルがある場合は取得しない。

    python scripts/fetch_webapp.py
"""

import urllib.request

from common import SOURCES_DIR

JAFFLE_SHOP_COMMIT = "fd7bfacae4f497ff044a6a0275268676bf1b64c3"
BASE_URL = f"https://raw.githubusercontent.com/dbt-labs/jaffle_shop/{JAFFLE_SHOP_COMMIT}/seeds"

# jaffle_shop の seed ファイル名 -> エクスポートファイル名
FILES = {
    "raw_customers.csv": "customers.csv",
    "raw_orders.csv": "orders.csv",
    "raw_payments.csv": "payments.csv",
}


def main():
    webapp_dir = SOURCES_DIR / "webapp"
    webapp_dir.mkdir(parents=True, exist_ok=True)
    for seed, export in FILES.items():
        path = webapp_dir / export
        if path.exists():
            continue
        with urllib.request.urlopen(f"{BASE_URL}/{seed}") as response:
            path.write_bytes(response.read())


if __name__ == "__main__":
    main()
