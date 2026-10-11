-- エクスポートファイルの取り込み先となる raw テーブル。
-- 各システムのエクスポート形式をそのまま保持し、取り込み時のメタデータ列（_source_file、_loaded_at）を付与する。

-- Web アプリ（顧客向け EC サイト）
create schema if not exists raw_webapp;

create table if not exists raw_webapp.customers (
    id integer,
    first_name text,
    last_name text,
    _source_file text,
    _loaded_at timestamptz default now()
);

create table if not exists raw_webapp.orders (
    id integer,
    user_id integer,
    order_date date,
    status text,
    _source_file text,
    _loaded_at timestamptz default now()
);

create table if not exists raw_webapp.payments (
    id integer,
    order_id integer,
    payment_method text,
    amount integer,
    _source_file text,
    _loaded_at timestamptz default now()
);

-- Google Analytics
create schema if not exists raw_ga;

create table if not exists raw_ga.events (
    event_date text,
    event_timestamp bigint,
    event_name text,
    user_pseudo_id text,
    user_id text,
    ga_session_id bigint,
    ga_session_number integer,
    page_location text,
    traffic_source text,
    traffic_medium text,
    traffic_campaign text,
    device_category text,
    transaction_id text,
    purchase_revenue numeric(10, 2),
    _source_file text,
    _loaded_at timestamptz default now()
);

-- CRM
create schema if not exists raw_crm;

create table if not exists raw_crm.contacts (
    contact_id text,
    external_customer_id integer,
    first_name text,
    last_name text,
    email text,
    phone text,
    birth_date date,
    membership_rank text,
    email_opt_in boolean,
    created_at timestamptz,
    updated_at timestamptz,
    _source_file text,
    _loaded_at timestamptz default now()
);

create table if not exists raw_crm.inquiries (
    inquiry_id text,
    contact_id text,
    order_id integer,
    category text,
    channel text,
    status text,
    created_at timestamptz,
    closed_at timestamptz,
    _source_file text,
    _loaded_at timestamptz default now()
);

create table if not exists raw_crm.campaigns (
    campaign_id text,
    campaign_name text,
    utm_campaign text,
    channel text,
    start_date date,
    end_date date,
    budget integer,
    _source_file text,
    _loaded_at timestamptz default now()
);
