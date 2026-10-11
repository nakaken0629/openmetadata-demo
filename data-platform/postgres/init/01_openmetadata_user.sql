-- OpenMetadata がメタデータを取り込むための読み取り専用ユーザー。
-- Postgres のデータディレクトリの初期化時（初回起動時）にだけ実行される。

create role openmetadata with login password 'openmetadata';
grant connect on database dwh to openmetadata;

-- loader と dbt は dwh ユーザーでスキーマ・テーブル・ビューを作成する。
-- 今後 dwh ユーザーが作成するスキーマとテーブル（ビューを含む）を、openmetadata ユーザーが参照できるようにする。
alter default privileges for role dwh grant usage on schemas to openmetadata;
alter default privileges for role dwh grant select on tables to openmetadata;

-- OpenMetadata は pg_stat_statements から実行されたクエリを取得し、利用状況（usage）とリネージを作成する。
-- pg_stat_statements は docker-compose.yml で shared_preload_libraries に指定して読み込んでいる。
-- 他のユーザー（dwh）が実行したクエリの本文を参照するには pg_read_all_stats ロールが必要。
create extension if not exists pg_stat_statements;
grant pg_read_all_stats to openmetadata;
