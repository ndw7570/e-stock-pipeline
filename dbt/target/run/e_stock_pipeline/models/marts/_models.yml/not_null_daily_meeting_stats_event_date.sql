select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select event_date
from "stock_db"."dbt_default_marts"."daily_meeting_stats"
where event_date is null



      
    ) dbt_internal_test