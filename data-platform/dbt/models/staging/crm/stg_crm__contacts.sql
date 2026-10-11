select
    contact_id,
    external_customer_id as customer_id,
    first_name,
    last_name,
    email,
    phone,
    birth_date,
    membership_rank,
    email_opt_in as is_email_opt_in,
    created_at,
    updated_at
from {{ source('crm', 'contacts') }}
