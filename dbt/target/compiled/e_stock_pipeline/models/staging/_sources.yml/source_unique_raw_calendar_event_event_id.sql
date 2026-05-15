
    
    

select
    event_id as unique_field,
    count(*) as n_records

from "stock_db"."google_workspace"."calendar_event"
where event_id is not null
group by event_id
having count(*) > 1


