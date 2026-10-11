select
    campaign_id,
    campaign_name,
    utm_campaign,
    channel,
    start_date,
    end_date,
    budget
from {{ source('crm', 'campaigns') }}
