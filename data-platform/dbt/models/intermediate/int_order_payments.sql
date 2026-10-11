-- 注文ごとに決済金額を支払い方法別に集計する
select
    order_id,
    coalesce(sum(amount) filter (where payment_method = 'credit_card'), 0) as credit_card_amount,
    coalesce(sum(amount) filter (where payment_method = 'coupon'), 0) as coupon_amount,
    coalesce(sum(amount) filter (where payment_method = 'bank_transfer'), 0) as bank_transfer_amount,
    coalesce(sum(amount) filter (where payment_method = 'gift_card'), 0) as gift_card_amount,
    sum(amount) as total_amount
from {{ ref('stg_webapp__payments') }}
group by order_id
