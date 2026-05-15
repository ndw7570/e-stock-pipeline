select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select meeting_count
from "stock_db"."dbt_default_marts"."daily_meeting_stats"
where meeting_count is null



      
    ) dbt_internal_test