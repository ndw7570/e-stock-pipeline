
  
    

  create  table "stock_db"."dbt_default_marts"."daily_meeting_stats__dbt_tmp"
  
  
    as
  
  (
    

-- 날짜별 / 주최자별 confirmed 미팅 건수 집계.
-- BI 도구나 Slack 리포트가 직접 조회하는 mart 레이어.

SELECT
    event_date,
    organizer_email,
    COUNT(*) AS meeting_count
FROM "stock_db"."dbt_default_staging"."stg_calendar_event"
WHERE status = 'confirmed'
GROUP BY event_date, organizer_email
ORDER BY event_date DESC, meeting_count DESC
  );
  