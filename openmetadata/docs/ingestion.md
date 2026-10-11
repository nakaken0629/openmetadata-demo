# データ基盤と Lightdash のメタデータの取り込み

OpenMetadata の UI から、データ基盤（`data-platform/`）と Lightdash（`lightdash/`）のメタデータを取り込む手順です。

## 前提条件

次の順に起動しておきます。OpenMetadata のサーバーと ingestion（Airflow）は、`docker-compose.override.yml` により共有ネットワーク `openmetadata-demo` に参加し、データ基盤の Postgres と Lightdash に接続できます。

1. `docker network create openmetadata-demo`（初回のみ）
2. データ基盤（`data-platform/` で `docker compose up --detach`）
3. Lightdash（`lightdash/` で `docker compose up --detach`）
4. OpenMetadata（このディレクトリで `docker compose up --detach`）

## 1. データ基盤（Postgres）の取り込み

### データベースサービスの作成

Settings > Services > Databases から、Postgres のサービスを追加します。

| 項目 | 値 |
| --- | --- |
| サービスの種類 | Postgres |
| ユーザー名 | `openmetadata` |
| 認証方式 / パスワード | Basic Auth / `openmetadata` |
| ホストとポート | `data_platform_postgres:5432` |
| データベース | `dwh` |

`openmetadata` ユーザーは、データ基盤の Postgres の初回起動時に作成される読み取り専用のユーザーです（`data-platform/postgres/init/01_openmetadata_user.sql`）。

接続テスト（Test Connection）が成功することを確認してから保存します。接続テストには、クエリの履歴（`pg_stat_statements`）を取得できるかの確認も含まれます。データ基盤の Postgres では `pg_stat_statements` を有効にしているため、利用状況（Usage）やクエリからのリネージ（Lineage）の取り込みも追加できます。

### メタデータの取り込み

作成したサービスにメタデータの取り込み（Metadata Ingestion）を追加し、デプロイして実行します。設定は既定値のままでかまいません。staging と intermediate のモデルはビューですが、ビューは既定で取り込まれます（取り込みの設定 `includeViews` の既定値が有効のため）。

次のスキーマが取り込まれます。

| スキーマ | 内容 |
| --- | --- |
| `raw_webapp`、`raw_ga`、`raw_crm` | エクスポートファイルを取り込んだ raw テーブル |
| `staging`、`intermediate`、`marts` | dbt のモデル |

### dbt の取り込み

メタデータの取り込みが完了した後、同じサービスに dbt の取り込み（dbt Ingestion）を追加し、デプロイして実行します。dbt の設定の取得元（dbt Configuration Source）には Local を選び、次のパスを指定します。

| 項目 | パス |
| --- | --- |
| dbt Catalog File Path | `/opt/dbt-artifacts/catalog.json` |
| dbt Manifest File Path | `/opt/dbt-artifacts/manifest.json` |
| dbt Run Results File Path | `/opt/dbt-artifacts/run_results.json` |

`/opt/dbt-artifacts` には、データ基盤の dbt の成果物（`data-platform/dbt/target/`）が読み取り専用でマウントされています。dbt の取り込みにより、モデルの説明・タグ・リネージ・SQL と、dbt のテストとその結果が OpenMetadata に反映されます。

## 2. Lightdash の取り込み

### API キーの作成

Lightdash（http://localhost:8090 、`admin@example.com` / `lightdash123`）にログインし、ユーザー設定の Personal access tokens から API キー（個人アクセストークン）を作成します。

### ダッシュボードサービスの作成

Settings > Services > Dashboards から、Lightdash のサービスを追加します。

| 項目 | 値 |
| --- | --- |
| サービスの種類 | Lightdash |
| ホストとポート | `http://lightdash:8090` |
| API キー | 作成した個人アクセストークン |
| プロジェクト UUID | Lightdash のプロジェクト「EC サイト分析」の UUID |
| スペース UUID | Lightdash のスペース「EC サイト分析」の UUID |

プロジェクト UUID とスペース UUID は、Lightdash の setup のログに出力されています。

```bash
docker logs lightdash_setup
```

接続テストが成功することを確認してから保存し、メタデータの取り込みを追加して実行します。スペース内のダッシュボード「EC サイト KPI」と、そのチャートが取り込まれます。

OpenMetadata 2.0.3 の Lightdash コネクタは、ダッシュボードとチャートからテーブルへのリネージを作成しません。
