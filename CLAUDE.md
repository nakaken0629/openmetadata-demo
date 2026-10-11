# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

プロジェクト概要は README.md を参照。サンプルを変更する際は、書籍の記述と食い違わないよう注意すること。

## リポジトリ構成

モノレポ構成。サブシステムはすべてローカルの Docker 上で動作する。

- `openmetadata/`: OpenMetadata 本体
- `data-platform/`: OpenMetadata に取り込むサンプルデータ基盤（dbt）
- `lightdash/`: Lightdash

作業時はどのサブシステムに対する変更かを意識し、各ディレクトリ内で完結させること。

## 言語

- ユーザーとのやり取りはすべて日本語で行うこと。
- ドキュメント、コメント、コミットメッセージなどの成果物もすべて日本語で作成すること（コード中の識別子やコマンドはこの限りではない）。
