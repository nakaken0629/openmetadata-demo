-- OpenMetadata がメタデータを取り込むための読み取り専用ユーザー。
-- Postgres のデータディレクトリの初期化時（初回起動時）にだけ実行される。

create role openmetadata with login password 'openmetadata';
grant connect on database dwh to openmetadata;

-- loader と dbt は dwh ユーザーでスキーマ・テーブル・ビューを作成する。
-- 今後 dwh ユーザーが作成するスキーマとテーブル（ビューを含む）を、openmetadata ユーザーが参照できるようにする。
alter default privileges for role dwh grant usage on schemas to openmetadata;
alter default privileges for role dwh grant select on tables to openmetadata;
