# Lightdash

データ基盤（`data-platform/`）の dbt プロジェクトを参照する BI ツール Lightdash をローカルの Docker 上で起動するための設定です。

## バージョン

- Lightdash: 2.565.0

`docker-compose.yml` は公式リポジトリの [docker-compose.yml](https://github.com/lightdash/lightdash/blob/2.565.0/docker-compose.yml) をもとに、次の点を変更しています。

- オブジェクトストレージを MinIO から [SeaweedFS](https://github.com/seaweedfs/seaweedfs)（Apache License 2.0）に置き換え
- headless-browser はビルドせず、公式の `Dockerfile.headless-browser` と同じイメージ（`ghcr.io/browserless/chromium:v2.49.0`）を直接使用
- イメージのバージョンを固定
- ポートを 8080 から 8090 に変更（OpenMetadata の Airflow と重複するため）
- データ基盤の dbt プロジェクトをマウントし、`openmetadata-demo` ネットワークに参加
- 使用しない環境変数（SSO、Slack、AI など）を削除
- プロジェクト名を `openmetadata-demo-lightdash` に明示（ディレクトリ名から決まる `lightdash` のままだと、他の Lightdash 環境とボリューム名が重複するため）

## 構成

| コンテナ | 概要 |
| --- | --- |
| `lightdash` | Lightdash 本体 |
| `lightdash_db` | Lightdash 自体のメタデータを保存する DB（Postgres） |
| `lightdash_seaweedfs` | S3 互換のオブジェクトストレージ（クエリ結果やエクスポートファイルの保存先） |
| `lightdash_seaweedfs_init` | SeaweedFS にバケットを作成する。完了後に終了する |
| `lightdash_headless_browser` | PDF・画像のエクスポートやスケジュール配信で使うヘッドレスブラウザ |
| `lightdash_setup` | 初期セットアップ（管理者ユーザー・組織・プロジェクトの作成と dbt プロジェクトのコンパイル）を行う。完了後に終了する |

Lightdash のイメージは amd64 のみ提供されているため、Apple Silicon の Mac ではエミュレーションで動作します（Colima の場合は `binfmt: true` または `rosetta: true`）。

## 前提条件

- データ基盤（`data-platform/`）が起動していること
- `openmetadata-demo` ネットワークが作成されていること（`docker network create openmetadata-demo`）

## 起動

このディレクトリで実行します。

```bash
docker compose up --detach
```

## アクセス先

| サービス | URL | ユーザー名 | パスワード |
| --- | --- | --- | --- |
| Lightdash | http://localhost:8090 | admin@example.com | lightdash123 |

## 初期セットアップ

起動時に setup（`setup/setup.py`）が Lightdash の API を使って、管理者ユーザー・組織・プロジェクトを次の内容で作成します。作成済みのものは作成を省略するため、何度起動しても同じ状態になります。最後に dbt プロジェクトをリフレッシュ（コンパイル）するため、起動のたびに dbt プロジェクトの変更が反映されます。

| 項目 | 値 |
| --- | --- |
| 組織 | EC Analytics |
| プロジェクト | EC サイト分析 |
| dbt の接続方法 | dbt local server（`/usr/app/dbt` にマウントしたデータ基盤の dbt プロジェクト、dbt v1.12） |
| ウェアハウス | PostgreSQL（ホスト `data_platform_postgres`、ポート 5432、データベース `dwh`、ユーザー `dwh`、スキーマ `marts`） |

Lightdash はマウントした dbt プロジェクトの `target/` には書き込まないため、データ基盤が出力する dbt の成果物（OpenMetadata に取り込むもの）には影響しません。

起動中に dbt プロジェクトを変更した場合は、setup を再実行して反映します。

```bash
docker compose run --rm setup
```

## 停止・削除

```bash
docker compose stop            # 停止（データは保持）
docker compose down            # コンテナを削除（データは保持）
docker compose down --volumes  # データ（名前付きボリューム）も削除
```
