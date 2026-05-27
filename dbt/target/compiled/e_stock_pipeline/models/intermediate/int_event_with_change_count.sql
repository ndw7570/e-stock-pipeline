-- intermediate 책임:
-- 1) staging 여러 개 JOIN
-- 2) 비즈니스 의미가 있는 집계/파생
-- 3) 재사용 가능한 building block (여러 mart가 ref할 것)
-- 절대 하지 말 것: BI 직접 노출, 너무 좁은 mart 로직

SELECT
    e.event_id,
    e.calendar_id,
    e.summary,
    e.status,
    e.start_time,
    e.organizer_email,

    -- changelog에서 집계한 변경 정보를 부착
    -- COALESCE(_, 0): 변경 이력 없는 이벤트도 0으로 노출 (LEFT JOIN이라 NULL 가능)
    COALESCE(c.total_changes, 0)    AS total_change_count,
    COALESCE(c.added_count, 0)      AS added_count,
    COALESCE(c.modified_count, 0)   AS modified_count,
    COALESCE(c.cancelled_count, 0)  AS cancelled_count,
    c.first_seen_at,
    c.last_change_at
FROM "stock_db"."dbt_default_staging"."stg_calendar_event" e
LEFT JOIN (
    -- 한 이벤트의 변경 이력을 집계
    SELECT
        event_id,
        COUNT(*)                                            AS total_changes,
        COUNT(*) FILTER (WHERE change_type = 'added')       AS added_count,
        COUNT(*) FILTER (WHERE change_type = 'modified')    AS modified_count,
        COUNT(*) FILTER (WHERE change_type = 'cancelled')   AS cancelled_count,
        MIN(observed_at)                                    AS first_seen_at,
        MAX(observed_at)                                    AS last_change_at
    FROM "stock_db"."dbt_default_staging"."stg_calendar_event_changelog"
    GROUP BY event_id
) c ON c.event_id = e.event_id