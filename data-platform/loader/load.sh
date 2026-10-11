#!/usr/bin/env bash
# エクスポートファイル（/sources 配下の CSV）を Postgres の raw テーブルに取り込む。
# 毎回 raw テーブルを空にしてから全ファイルを取り込み直す（全件洗い替え）。
# 接続先は環境変数 PGHOST / PGUSER / PGPASSWORD / PGDATABASE で指定する。
set -euo pipefail

SOURCES_DIR=/sources

psql -v ON_ERROR_STOP=1 --quiet -f /loader/tables.sql

# <テーブル> <ファイル> の組を受け取り、\copy と _source_file の更新を行う SQL を出力する
copy_sql() {
    local table=$1 file=$2
    echo "\\copy ${table} ($(head -n 1 "${file}")) from '${file}' with (format csv, header true)"
    echo "update ${table} set _source_file = '$(basename "${file}")' where _source_file is null;"
}

{
    echo "truncate raw_webapp.customers, raw_webapp.orders, raw_webapp.payments, raw_ga.events, raw_crm.contacts, raw_crm.inquiries, raw_crm.campaigns;"
    for name in customers orders payments; do
        copy_sql "raw_webapp.${name}" "${SOURCES_DIR}/webapp/${name}.csv"
    done
    for file in "${SOURCES_DIR}"/ga/events_*.csv; do
        copy_sql raw_ga.events "${file}"
    done
    for name in contacts inquiries campaigns; do
        copy_sql "raw_crm.${name}" "${SOURCES_DIR}/crm/${name}.csv"
    done
} | psql -v ON_ERROR_STOP=1 --quiet --single-transaction

psql --quiet --no-align --tuples-only -c "
select table_schema || '.' || table_name || ': ' || (xpath('/row/c/text()', query_to_xml('select count(*) as c from ' || table_schema || '.' || table_name, false, true, '')))[1]::text || ' rows'
from information_schema.tables
where table_schema like 'raw\_%'
order by 1"
