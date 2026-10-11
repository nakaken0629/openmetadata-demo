"""エクスポートファイル生成スクリプトの共通処理。"""

import csv
from datetime import timedelta, timezone
from pathlib import Path

# 乱数のシード。固定しているため、何度実行しても同じファイルが生成される
SEED = 42
SOURCES_DIR = Path(__file__).resolve().parent.parent / "sources"
JST = timezone(timedelta(hours=9))


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
