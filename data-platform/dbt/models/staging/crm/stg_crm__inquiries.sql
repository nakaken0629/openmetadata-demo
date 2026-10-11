select
    inquiry_id,
    contact_id,
    order_id,
    category,
    channel,
    status,
    created_at,
    closed_at
from {{ source('crm', 'inquiries') }}
