with sessions as (
    select * from {{ ref('int_sessions') }}
),

-- ログインしたことのあるブラウザは、ログインしていないセッションもその顧客のものとみなす
pseudo_customers as (
    select distinct on (user_pseudo_id)
        user_pseudo_id,
        customer_id
    from sessions
    where customer_id is not null
    order by user_pseudo_id, session_started_at
),

campaigns as (
    select * from {{ ref('stg_crm__campaigns') }}
)

select
    sessions.session_key,
    sessions.user_pseudo_id,
    coalesce(sessions.customer_id, pseudo_customers.customer_id) as customer_id,
    sessions.session_number,
    sessions.session_date,
    sessions.session_started_at,
    sessions.session_ended_at,
    extract(epoch from sessions.session_ended_at - sessions.session_started_at)::integer as duration_seconds,
    sessions.traffic_source,
    sessions.traffic_medium,
    campaigns.campaign_id,
    sessions.device_category,
    sessions.page_views,
    sessions.item_views,
    sessions.is_converted,
    sessions.order_id,
    sessions.purchase_revenue
from sessions
left join pseudo_customers using (user_pseudo_id)
left join campaigns on sessions.traffic_campaign = campaigns.utm_campaign
