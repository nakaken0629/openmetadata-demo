with inquiries as (
    select * from {{ ref('stg_crm__inquiries') }}
),

contacts as (
    select * from {{ ref('stg_crm__contacts') }}
)

select
    inquiries.inquiry_id,
    inquiries.contact_id,
    contacts.customer_id,
    inquiries.order_id,
    inquiries.category,
    inquiries.channel,
    inquiries.status,
    inquiries.created_at,
    inquiries.closed_at,
    round((extract(epoch from inquiries.closed_at - inquiries.created_at) / 3600)::numeric, 1) as resolution_hours
from inquiries
left join contacts using (contact_id)
