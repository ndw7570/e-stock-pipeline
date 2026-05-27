
  
    

  create  table "stock_db"."dbt_default_mart_core"."dim_organizer__dbt_tmp"
  
  
    as
  
  (
    -- =====================================================
-- 차원: 한 row = 한 주최자(organizer_email)
-- Grain: organizer_email
-- 출처: stg_calendar_event에서 organizer를 추출/집계
-- 용도: 모든 fact가 이 차원을 JOIN해서 주최자 속성 활용
-- =====================================================

SELECT
    organizer_email                                       AS organizer_email,         -- 자연키 (Natural Key)
    SPLIT_PART(organizer_email, '@', 1)                   AS organizer_local_name,    -- 이메일 앞부분 (e.g. 'ji.lee')
    SPLIT_PART(organizer_email, '@', 2)                   AS organizer_domain,        -- 도메인 (e.g. 'interxlab.com')

    -- 활동 통계 (차원이지만 derived attribute로 포함)
    COUNT(*)                                              AS total_meetings_organized,
    COUNT(DISTINCT calendar_id)                           AS distinct_calendars,
    MIN(start_time)                                       AS first_meeting_at,
    MAX(start_time)                                       AS last_meeting_at

FROM "stock_db"."dbt_default_staging"."stg_calendar_event"
WHERE organizer_email IS NOT NULL                          -- 자연키 NULL 제외
GROUP BY organizer_email
  );
  