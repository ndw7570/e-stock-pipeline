-- =====================================================
-- Fact: 한 row = 한 미팅 (event_id)
-- Grain: event_id
-- Measure: duration_min, is_cancelled (집계 가능)
-- FK: organizer_email → dim_organizer
--     calendar_id    → dim_calendar (미래)
-- Degenerate Dimension: event_id, status
-- =====================================================

SELECT
    -- 자연키 (degenerate dimension)
    event_id,

    -- FK (차원 참조)
    organizer_email,
    calendar_id,

    -- 사실 속성 (분석 축으로 자주 쓰는 텍스트들 — degenerate dim)
    status,

    -- 시간 (이것도 차원, 미래 dim_date FK로)
    start_time,
    end_time,
    event_date,

    -- Measure (집계 가능한 숫자)
    EXTRACT(EPOCH FROM (end_time - start_time)) / 60     AS duration_min,
    CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END     AS is_cancelled,
    CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END     AS is_confirmed,
    1                                                     AS meeting_count   -- 항상 1 (SUM=건수)

FROM "stock_db"."dbt_default_staging"."stg_calendar_event"
WHERE event_id IS NOT NULL                                                   -- grain 보장