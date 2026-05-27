from __future__ import annotations

from app.monitoring_google_workspace_logs.services.collectors.sinks.calendar_database import (
    write_changes_to_database,
)
from app.monitoring_google_workspace_logs.services.collectors.sources.calendar_google_api import (
    CalendarChange,
)
from app.monitoring_google_workspace_logs.services.collectors.sources.calendar_kafka import (
    consume_calendar_changes,
)


def consume_to_database(group_id: str = "calendar-to-database") -> dict[str, int]:
    """
    모드 C의 Consumer 측 비즈니스 로직.
    Kafka topic에서 변경 이벤트를 consume → DB에 적재.

    Returns:
        {'consumed': 적재 건수, 'skipped': 옛 형식 skip 건수}
    """
    consumed = 0
    skipped = 0

    for msg in consume_calendar_changes(group_id=group_id):
        # 옛 형식(구조화 안 된) 메시지 방어
        if "event" not in msg or "calendar_id" not in msg:
            skipped += 1
            continue

        change = CalendarChange(
            event=msg["event"],
            calendar_id=msg["calendar_id"],
            change_type=msg["change_type"],
        )
        write_changes_to_database([change])
        consumed += 1

    return {"consumed": consumed, "skipped": skipped}