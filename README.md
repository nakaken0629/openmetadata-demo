# openmetadata-demo

技術書典21で頒布した OpenMetadata 本の中で利用しているサンプルを管理するリポジトリです。

## 構成

モノレポ構成で、以下の3つのサブシステムから成ります。すべてローカルの Docker 上で動作します。

```
.
├── openmetadata/    # OpenMetadata 本体
├── data-platform/   # OpenMetadata に取り込むサンプルデータ基盤（dbt）
└── lightdash/       # BI ツール Lightdash（データ基盤の dbt プロジェクトを参照）
```

| ディレクトリ | サブシステム | 概要 |
| --- | --- | --- |
| `openmetadata/` | OpenMetadata 本体 | メタデータ管理基盤。データ基盤・Lightdash からメタデータを取り込む |
| `data-platform/` | データ基盤 | dbt によるサンプルデータ基盤 |
| `lightdash/` | Lightdash | データ基盤上の BI ツール |
