
    
    

with all_values as (

    select
        status as value_field,
        count(*) as n_records

    from "stock_db"."dbt_default_staging"."stg_calendar_event"
    group by status

)

select *
from all_values
where value_field not in (
    'confirmed','tentative','cancelled'
)


