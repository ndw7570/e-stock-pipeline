

-- staging 책임:
-- 1) raw → 정제 (1:1)
-- 2) 시간대 변환 (UTC → KST 파생 컬럼 추가)
-- 3) 분석에 편한 파생 컬럼 (날짜만 추출)
-- 절대 하지 말 것: JOIN, 집계, 비즈니스 룰

SELECT
    id,
    event_id,
    calendar_id,
    change_type,
    event_summary,
    event_status,
    event_start_time,                             -- UTC 그대로 (raw 충실)
    event_end_time,
    observed_at,                                  -- UTC (raw)
    -- 파생 컬럼: KST 변환 (분석에서 자주 씀)
    (observed_at AT TIME ZONE 'Asia/Seoul')         AS observed_at_kst,
    DATE(observed_at AT TIME ZONE 'Asia/Seoul')     AS observed_date_kst
FROM "stock_db"."google_workspace"."calendar_event_changelog"