# OpenMetadata

OpenMetadata 本体をローカルの Docker 上で起動するための設定です。

[公式ドキュメント（Local Docker Deployment）](https://docs.open-metadata.org/v2.0.x/quick-start/local-docker-deployment) の手順に従っています。

## バージョン

- OpenMetadata: 2.0.3
- DB: MySQL

`docker-compose.yml` は公式リリースで配布されているファイルを無改変で配置しています。

```bash
curl -sL -o docker-compose.yml https://github.com/open-metadata/OpenMetadata/releases/download/2.0.3-release/docker-compose.yml
```

## 前提条件

- Docker 20.10.0 以上
- Docker Compose v2.1.1 以上
- Docker に割り当てるリソース: メモリ 6 GiB 以上、vCPU 4 以上

## 起動

このディレクトリで実行します。

```bash
docker compose up --detach
```

以下のコンテナが起動します（`execute_migrate_all` は DB マイグレーション用で、完了後に終了します）。

- `openmetadata_server`
- `openmetadata_ingestion`
- `openmetadata_elasticsearch`
- `openmetadata_mysql`

## アクセス先

| サービス | URL | ユーザー名 | パスワード |
| --- | --- | --- | --- |
| OpenMetadata UI | http://localhost:8585 | admin@open-metadata.org | admin |
| Airflow（Ingestion） | http://localhost:8080 | admin | admin |

その他、MySQL（3306）、Elasticsearch（9200 / 9300）、OpenMetadata の管理用ポート（8586）もホストに公開されます。

## 停止・削除

```bash
docker compose stop            # 停止（データは保持）
docker compose start           # 再開
docker compose down            # コンテナを削除（データは保持）
docker compose down --volumes  # 名前付きボリュームも削除
```

MySQL のデータは `docker-compose.override.yml` により名前付きボリューム（`openmetadata_db-data`）に保存されるため、`docker compose down --volumes` で完全に初期化されます。
