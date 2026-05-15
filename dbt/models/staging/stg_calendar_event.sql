{{ config(materialized='view') }}

-- 원본 calendar_event 테이블에서 삭제 안 된 이벤트만 추출하고,
-- 분석에 자주 쓰이는 event_date(시작일) 컬럼을 미리 계산해서 노출한다.

SELECT
    event_id,
    calendar_id,
    summary,
    status,
    start_time,
    end_time,
    organizer_email,
    DATE(start_time) AS event_date,
    created_at,
    updated_at
FROM {{ source('raw', 'calendar_event') }}
WHERE is_deleted = FALSE
