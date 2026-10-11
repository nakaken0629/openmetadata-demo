with campaigns as (
    select * from {{ ref('stg_crm__campaigns') }}
),

campaign_sessions as (
    select
        campaign_id,
        count(*) as number_of_sessions,
        count(*) filter (where is_converted) as number_of_conversions
    from {{ ref('fct_sessions') }}
    where campaign_id is not null
    group by campaign_id
),

campaign_orders as (
    select
        campaign_id,
        sum(amount) as revenue
    from {{ ref('fct_orders') }}
    where campaign_id is not null
    group by campaign_id
)

select
    campaigns.campaign_id,
    campaigns.campaign_name,
    campaigns.utm_campaign,
    campaigns.channel,
    campaigns.start_date,
    campaigns.end_date,
    campaigns.budget,
    coalesce(campaign_sessions.number_of_sessions, 0) as number_of_sessions,
    coalesce(campaign_sessions.number_of_conversions, 0) as number_of_conversions,
    coalesce(campaign_orders.revenue, 0) as revenue
from campaigns
left join campaign_sessions using (campaign_id)
left join campaign_orders using (campaign_id)
