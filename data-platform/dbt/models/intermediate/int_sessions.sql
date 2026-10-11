-- GA のイベントをセッション単位に集約する
with events as (
    select * from {{ ref('stg_ga__events') }}
),

sessions as (
    select
        session_key,
        user_pseudo_id,
        max(customer_id) as customer_id,
        min(session_number) as session_number,
        min(event_at) as session_started_at,
        max(event_at) as session_ended_at,
        count(*) filter (where event_name = 'page_view') as page_views,
        count(*) filter (where event_name = 'view_item') as item_views,
        max(order_id) as order_id,
        coalesce(sum(purchase_revenue), 0) as purchase_revenue
    from events
    group by session_key, user_pseudo_id
),

-- 流入元とデバイスはセッション最初のイベントの値を使う
first_events as (
    select distinct on (session_key)
        session_key,
        event_date as session_date,
        traffic_source,
        traffic_medium,
        traffic_campaign,
        device_category
    from events
    order by session_key, event_at
)

select
    sessions.session_key,
    sessions.user_pseudo_id,
    sessions.customer_id,
    sessions.session_number,
    first_events.session_date,
    sessions.session_started_at,
    sessions.session_ended_at,
    first_events.traffic_source,
    first_events.traffic_medium,
    first_events.traffic_campaign,
    first_events.device_category,
    sessions.page_views,
    sessions.item_views,
    sessions.order_id is not null as is_converted,
    sessions.order_id,
    sessions.purchase_revenue
from sessions
inner join first_events using (session_key)
