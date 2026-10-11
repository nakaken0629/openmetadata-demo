select
    to_date(event_date, 'YYYYMMDD') as event_date,
    to_timestamp(event_timestamp / 1000000.0) as event_at,
    event_name,
    user_pseudo_id,
    user_id::integer as customer_id,
    user_pseudo_id || '-' || ga_session_id as session_key,
    ga_session_number as session_number,
    -- サイトの URL を除いたパス
    regexp_replace(page_location, '^https?://[^/]+', '') as page_path,
    traffic_source,
    traffic_medium,
    nullif(traffic_campaign, '') as traffic_campaign,
    device_category,
    transaction_id::integer as order_id,
    purchase_revenue
from {{ source('ga', 'events') }}
