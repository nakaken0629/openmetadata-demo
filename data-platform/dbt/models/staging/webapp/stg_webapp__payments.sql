select
    id as payment_id,
    order_id,
    payment_method,
    -- セント単位からドル単位に変換する
    amount / 100.0 as amount
from {{ source('webapp', 'payments') }}
