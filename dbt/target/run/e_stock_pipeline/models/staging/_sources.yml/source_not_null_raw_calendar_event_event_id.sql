select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select event_id
from "stock_db"."google_workspace"."calendar_event"
where event_id is null



      
    ) dbt_internal_test