# docker-compose.override.yml を追加した理由

## 概要

公式配布の `docker-compose.yml` では、MySQL のデータディレクトリ `/var/lib/mysql` はホストの `./docker-volume/db-data` にバインドマウントされます。

```yaml
services:
  mysql:
    volumes:
     - ./docker-volume/db-data:/var/lib/mysql
```

本リポジトリでは `docker-compose.yml` を無改変のまま、`docker-compose.override.yml` でこのマウント先を名前付きボリューム `db-data`（実体は `openmetadata_db-data`）に置き換えています。

```yaml
volumes:
  db-data:
services:
  mysql:
    volumes:
      - db-data:/var/lib/mysql
```

## 経緯

macOS 上でバインドマウントのまま起動したところ、DB マイグレーション（`execute_migrate_all`）が次のエラーで失敗しました。

```
Got error 168 from storage engine
```

このため、データディレクトリを名前付きボリュームに置き換える `docker-compose.override.yml` を追加しました。

## 検証結果

### 検証環境

- macOS（Apple Silicon）
- Colima（vmType: `vz`、mountType: `virtiofs`）
- Docker Engine 27.4.0
- MySQL 8.0.32（`docker.getcollate.io/openmetadata/db:2.0.3`）

### バインドマウントと名前付きボリュームの比較

| 項目 | バインドマウント | 名前付きボリューム |
| --- | --- | --- |
| `lower_case_table_names` | 2 | 0 |
| `lower_case_file_system` | 1 | 0 |
| 大文字を含むテーブル名での CREATE / ALTER / RENAME | 成功（ファイル名は小文字で保存） | 成功 |

バインドマウントの場合、MySQL の起動ログに次の警告が出力されます。

```
[Warning] [MY-010159] [Server] Setting lower_case_table_names=2 because file system for /var/lib/mysql/ is case insensitive
```

macOS のファイルシステム（APFS の既定設定）は大文字・小文字を区別しないため、これをマウントしたデータディレクトリでは MySQL が `lower_case_table_names=2` で動作します。Linux 上の通常の動作（`0`）とは異なる設定になります。

### マイグレーションの再現確認

空のディレクトリをバインドマウントした状態で OpenMetadata 2.0.3 のマイグレーションを実行したところ、正常に完了しました（終了コード 0、`openmetadata_db` に 200 テーブル作成、`SERVER_CHANGE_LOG` の最大バージョン 2.0.3）。Error 168 は再現しませんでした。

## 原因について

Error 168 の原因は特定できていません。考えられる要因は次のとおりです（いずれも未検証）。

- 以前の実行で途中まで進んだデータが `./docker-volume/db-data` に残っており、その状態からの再実行で失敗した
- Docker の実行環境（ファイル共有の方式）の違い
- virtiofs 側の一時的な不具合

Error 168 は MySQL の汎用的な内部エラー（`HA_ERR_INTERNAL_ERROR`）で、ファイル操作の不整合などでも発生します。

## OpenMetadata の issue

OpenMetadata の GitHub リポジトリに、Error 168 を直接報告した issue は見つかりませんでした。関連するものは次のとおりです。

| issue / PR | 内容 |
| --- | --- |
| [#15177](https://github.com/open-metadata/OpenMetadata/issues/15177)（v1.3.0） | macOS で公式手順のとおりに起動すると MySQL が起動しない。`lower_case_table_names=2` の警告に続き、`Can't change data directory owner to mysql` で失敗。修正されないまま Close |
| [#17677](https://github.com/open-metadata/OpenMetadata/issues/17677)（v1.5.1） | #15177 と同じ問題の再報告。Slack での質問を案内されて Close |
| [#26048](https://github.com/open-metadata/OpenMetadata/issues/26048) / [PR #27234](https://github.com/open-metadata/OpenMetadata/pull/27234) | 新規インストール中に失敗すると Flowable のテーブルが中途半端な状態で残り、再実行しても復旧できない問題。2026-04 に修正 |

macOS でのバインドマウントに起因する問題は v1.3 の頃から報告されていますが、公式の対応はなく、`docker-compose.yml` は現在もバインドマウントのままです。

## 結論

原因は特定できていませんが、macOS では MySQL がファイルシステムの違いにより Linux と異なる設定（`lower_case_table_names=2`）で動作することを確認しました。こうした差異による問題を避けるため、データディレクトリを Docker の VM 内に置く名前付きボリュームを使用しています。

なお、名前付きボリュームを使用するため、MySQL のデータは `docker compose down --volumes` で削除されます。
