# データ基盤

OpenMetadata に取り込むサンプルのデータ基盤です。架空の EC サイトのデータを分析することを想定しています。

## 想定するシステム

EC サイトには次の 3 つのシステムがあり、いずれも定期的にデータをファイルにエクスポートしています。システムそのものは構築せず、エクスポートされたファイル（`sources/` 配下）をデータ基盤のソースとします。エクスポートファイルは起動時に generator が用意します（Git 管理対象外）。

| システム | 概要 | エクスポートファイル |
| --- | --- | --- |
| Web アプリ | 顧客向けの EC サイト | `sources/webapp/`（`customers.csv`、`orders.csv`、`payments.csv`） |
| Google Analytics | EC サイトのアクセス解析 | `sources/ga/events_YYYYMMDD.csv`（日次） |
| CRM | 社内の顧客管理システム | `sources/crm/`（`contacts.csv`、`inquiries.csv`、`campaigns.csv`） |

各システムのデータは次のように対応しています。

- Web アプリの顧客 ID（`customers.id`）は、GA の `user_id`（購入時のログイン後に付与）、CRM の `contacts.external_customer_id` と対応します。
- GA の `transaction_id` は、Web アプリの注文 ID（`orders.id`）と対応します。
- GA の `traffic_campaign` は、CRM の `campaigns.utm_campaign` と対応します。
- 一部の会員は CRM に登録されておらず、CRM には会員登録していない見込み客も含まれます。

## 構成

```
jaffle_shop (GitHub)
   │  generator（取得・生成）
   ▼
sources/ (エクスポートファイル)
   │  loader
   ▼
Postgres (dwh データベース)
   ├── raw_webapp
   ├── raw_ga
   └── raw_crm
```

| コンテナ | 概要 |
| --- | --- |
| `data_platform_postgres` | DWH（Postgres 17） |
| `data_platform_generator` | エクスポートファイルを用意する。完了後に終了する |
| `data_platform_loader` | エクスポートファイルを raw テーブルに取り込む。取り込み完了後に終了する |

loader は毎回 raw テーブルを空にしてから全ファイルを取り込み直します。各 raw テーブルには、取り込み元のファイル名（`_source_file`）と取り込み日時（`_loaded_at`）の列が付与されます。

## 起動

OpenMetadata・Lightdash と共有する Docker ネットワークを作成します（初回のみ）。

```bash
docker network create openmetadata-demo
```

このディレクトリで実行します。

```bash
docker compose up --detach
```

generator がエクスポートファイルを用意し、Postgres の起動後に loader がそれを取り込んで終了します。取り込み直す場合は次を実行します。

```bash
docker compose run --rm loader
```

## 接続情報

| 項目 | 値 |
| --- | --- |
| ホスト | `localhost`（ホストから） / `data_platform_postgres`（`openmetadata-demo` ネットワークから） |
| ポート | 5432 |
| データベース | `dwh` |
| ユーザー名 / パスワード | `dwh` / `dwh` |

## 停止・削除

```bash
docker compose stop            # 停止（データは保持）
docker compose down            # コンテナを削除（データは保持）
docker compose down --volumes  # データ（名前付きボリューム）も削除
```

## エクスポートファイルの用意

generator は次のスクリプトを順に実行します。GA は CRM のキャンペーンを参照するため、CRM の後に実行します。

| スクリプト | 概要 |
| --- | --- |
| `scripts/fetch_webapp.py` | Web アプリのエクスポートファイルを取得する（すでにある場合は取得しない） |
| `scripts/generate_crm.py` | Web アプリのデータをもとに CRM のエクスポートファイルを生成する |
| `scripts/generate_ga.py` | Web アプリのデータと CRM のキャンペーンをもとに GA のエクスポートファイルを生成する |

取得元のコミットと乱数のシードを固定しているため、何度実行しても同じファイルが用意されます。

## サンプルデータの出典

Web アプリのエクスポートファイル（`sources/webapp/*.csv`）は、[dbt-labs/jaffle_shop](https://github.com/dbt-labs/jaffle_shop)（Apache License 2.0）の seeds（`raw_customers.csv`、`raw_orders.csv`、`raw_payments.csv`）を、ファイル名を変更して使用しています。
