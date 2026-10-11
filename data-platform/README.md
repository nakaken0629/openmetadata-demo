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
   ├── raw_webapp ─┐
   ├── raw_ga     ─┼─ dbt ─→ staging → intermediate → marts
   └── raw_crm    ─┘
```

| コンテナ | 概要 |
| --- | --- |
| `data_platform_postgres` | DWH（Postgres 17） |
| `data_platform_generator` | エクスポートファイルを用意する。完了後に終了する |
| `data_platform_loader` | エクスポートファイルを raw テーブルに取り込む。取り込み完了後に終了する |
| `data_platform_dbt` | dbt（dbt-core 1.12 / dbt-postgres 1.11）でモデルの構築・テストとドキュメント生成を行う。完了後に終了する |

loader は毎回 raw テーブルを空にしてから全ファイルを取り込み直します。各 raw テーブルには、取り込み元のファイル名（`_source_file`）と取り込み日時（`_loaded_at`）の列が付与されます。

## dbt プロジェクト

dbt プロジェクトは `dbt/` にあります。モデルは層ごとに別のスキーマに作成されます。

| 層 | スキーマ | 形式 | モデル |
| --- | --- | --- | --- |
| staging | `staging` | ビュー | ソース（raw テーブル）ごとに列名・型を整えたもの（`stg_webapp__*`、`stg_ga__events`、`stg_crm__*`） |
| intermediate | `intermediate` | ビュー | `int_sessions`（GA のイベントをセッション単位に集約）、`int_order_payments`（注文ごとの決済金額を支払い方法別に集計） |
| marts | `marts` | テーブル | 下表 |

| marts のモデル | 概要 |
| --- | --- |
| `dim_customers` | 顧客。Web アプリの会員に CRM の顧客情報と、注文・セッション・問い合わせの集計値を統合した顧客 360 ビュー |
| `dim_campaigns` | マーケティングキャンペーン。キャンペーン経由のセッション数・購入数・売上を含む |
| `fct_orders` | 注文。決済金額と、購入したセッションの流入元を含む |
| `fct_sessions` | EC サイトへの訪問（セッション） |
| `fct_inquiries` | 問い合わせ |

`dim_customers.contact_id` の not_null テストは、CRM に登録されていない会員（8 名）を検出するため警告（WARN）になります。

marts のモデルには、Lightdash で使うメトリクス（売上、注文数、コンバージョン率など）とモデル間の結合を `config.meta` に定義しています（`models/marts/_marts__models.yml`）。

dbt コンテナは `dbt build` の後に `dbt docs generate --no-compile` を実行し、`dbt/target/` に次の成果物を出力します。`--no-compile` を付けないと、`run_results.json` が docs generate の結果で上書きされ、テスト結果が失われます。

| ファイル | 内容 |
| --- | --- |
| `manifest.json` | プロジェクトの定義（モデル、ソース、テスト、リネージ、説明など） |
| `catalog.json` | DWH 上のテーブル・列の情報 |
| `run_results.json` | `dbt build` の実行結果（テスト結果を含む） |

dbt のコマンドを個別に実行する場合は次のようにします。

```bash
docker compose run --rm dbt dbt build
docker compose run --rm dbt dbt docs generate --no-compile
```

## 起動

OpenMetadata・Lightdash と共有する Docker ネットワークを作成します（初回のみ）。

```bash
docker network create openmetadata-demo
```

このディレクトリで実行します。

```bash
docker compose up --detach
```

generator がエクスポートファイルを用意し、Postgres の起動後に loader がそれを取り込みます。その後 dbt がモデルの構築・テストとドキュメント生成を行って終了します。

取り込みからやり直す場合は次を実行します（generator と loader も実行されます）。

```bash
docker compose run --rm dbt
```

## 接続情報

| 項目 | 値 |
| --- | --- |
| ホスト | `localhost`（ホストから） / `data_platform_postgres`（`openmetadata-demo` ネットワークから） |
| ポート | 5432 |
| データベース | `dwh` |
| ユーザー名 / パスワード | `dwh` / `dwh` |
| 読み取り専用ユーザー（OpenMetadata 用） | `openmetadata` / `openmetadata` |

読み取り専用ユーザーは、Postgres の初回起動時に `postgres/init/01_openmetadata_user.sql` で作成されます。`dwh` ユーザーが作成するすべてのスキーマ・テーブル・ビューを参照できます。

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
