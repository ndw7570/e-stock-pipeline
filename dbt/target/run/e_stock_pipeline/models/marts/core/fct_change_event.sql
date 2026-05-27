
  
    

  create  table "stock_db"."dbt_default_mart_core"."fct_change_event__dbt_tmp"
  
  
    as
  
  (
    -- =====================================================
-- Fact: 한 row = 한 변경 발생 (changelog id)
-- Grain: changelog.id (append-only PK)
-- Measure: change_count (=1, 집계용)
-- Degenerate Dim: event_id, change_type
-- =====================================================

SELECT
    -- 자연키
    id                                                   AS change_event_id,

    -- Degenerate dimensions (별도 dim 테이블 없음)
    event_id,
    calendar_id,
    change_type,                                          -- added/modified/cancelled

    -- 시간 (degenerate)
    observed_at,
    observed_at_kst,
    observed_date_kst,

    -- 이벤트 시점 정보 (변경 발생 당시 사진)
    event_summary,
    event_status,

    -- Measure
    1                                                     AS change_count,
    CASE WHEN change_type = 'added'     THEN 1 ELSE 0 END AS is_added,
    CASE WHEN change_type = 'modified'  THEN 1 ELSE 0 END AS is_modified,
    CASE WHEN change_type = 'cancelled' THEN 1 ELSE 0 END AS is_cancelled

FROM "stock_db"."dbt_default_staging"."stg_calendar_event_changelog"
  );
  