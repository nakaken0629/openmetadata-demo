with orders as (
    select * from {{ ref('stg_webapp__orders') }}
),

payments as (
    select * from {{ ref('int_order_payments') }}
),

-- 購入したセッション（GA の purchase イベントの transaction_id で注文と対応する）
purchase_sessions as (
    select * from {{ ref('int_sessions') }}
    where is_converted
),

campaigns as (
    select * from {{ ref('stg_crm__campaigns') }}
)

select
    orders.order_id,
    orders.customer_id,
    orders.order_date,
    orders.status,
    coalesce(payments.credit_card_amount, 0) as credit_card_amount,
    coalesce(payments.coupon_amount, 0) as coupon_amount,
    coalesce(payments.bank_transfer_amount, 0) as bank_transfer_amount,
    coalesce(payments.gift_card_amount, 0) as gift_card_amount,
    coalesce(payments.total_amount, 0) as amount,
    purchase_sessions.session_key,
    purchase_sessions.traffic_source,
    purchase_sessions.traffic_medium,
    campaigns.campaign_id,
    purchase_sessions.device_category
from orders
left join payments using (order_id)
left join purchase_sessions using (order_id)
left join campaigns on purchase_sessions.traffic_campaign = campaigns.utm_campaign
