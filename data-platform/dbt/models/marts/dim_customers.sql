with customers as (
    select * from {{ ref('stg_webapp__customers') }}
),

contacts as (
    select * from {{ ref('stg_crm__contacts') }}
    where customer_id is not null
),

customer_orders as (
    select
        customer_id,
        min(order_date) as first_order_date,
        max(order_date) as most_recent_order_date,
        count(*) as number_of_orders,
        sum(amount) as lifetime_value
    from {{ ref('fct_orders') }}
    group by customer_id
),

customer_sessions as (
    select
        customer_id,
        count(*) as number_of_sessions
    from {{ ref('fct_sessions') }}
    where customer_id is not null
    group by customer_id
),

customer_inquiries as (
    select
        customer_id,
        count(*) as number_of_inquiries
    from {{ ref('fct_inquiries') }}
    where customer_id is not null
    group by customer_id
)

select
    customers.customer_id,
    customers.first_name,
    customers.last_name,
    contacts.contact_id,
    contacts.email,
    contacts.phone,
    contacts.birth_date,
    contacts.membership_rank,
    contacts.is_email_opt_in,
    customer_orders.first_order_date,
    customer_orders.most_recent_order_date,
    coalesce(customer_orders.number_of_orders, 0) as number_of_orders,
    coalesce(customer_orders.lifetime_value, 0) as lifetime_value,
    coalesce(customer_sessions.number_of_sessions, 0) as number_of_sessions,
    coalesce(customer_inquiries.number_of_inquiries, 0) as number_of_inquiries
from customers
left join contacts using (customer_id)
left join customer_orders using (customer_id)
left join customer_sessions using (customer_id)
left join customer_inquiries using (customer_id)
