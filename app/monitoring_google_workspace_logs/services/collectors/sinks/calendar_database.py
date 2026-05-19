from __future__ import annotations

from datetime import datetime
from typing import Any

from app.monitoring_google_workspace_logs.services.collectors.sources.calendar_google_api import (
    CalendarChange,
)
from app.monitoring_google_workspace_logs.services.database.handle_calendar_event import (
    CalendarEventService,
)
from app.monitoring_google_workspace_logs.services.database.handle_calendar_event_changelog import (
    CalendarEventChangelogService,
)
from app.monitoring_google_workspace_logs.services.database.model.calendar_event import (
    CalendarEventModel,
)
from app.monitoring_google_workspace_logs.services.database.model.calendar_event_changelog import (
    CHANGE_TYPE_CANCELLED,
    CalendarEventChangelogModel,
)


def write_changes_to_database(changes: list[CalendarChange]) -> dict[str, int]:
    """
    변경 이벤트들을 DB에 적재한다.
    - changelog 테이블: 이력 영구 보존 (append-only)
    - calendar_event 테이블: 현재 상태 갱신 (UPSERT)

    Returns:
        change_type별 처리 건수.
    """
    counts: dict[str, int] = {"added": 0, "modified": 0, "cancelled": 0}

    for change in changes:
        event = change.event
        calendar_id = change.calendar_id
        change_type = change.change_type

        # 1. changelog INSERT (이력)
        CalendarEventChangelogService.insert_change(
            CalendarEventChangelogModel(
                event_id=event["id"],
                calendar_id=calendar_id,
                change_type=change_type,
                event_summary=event.get("summary"),
                event_status=event.get("status"),
                event_start_time=_parse_event_datetime(event.get("start")),
                event_end_time=_parse_event_datetime(event.get("end")),
                raw_payload=event,
            )
        )

        # 2. calendar_event UPSERT (현재 상태)
        CalendarEventService.upsert_event(
            CalendarEventModel(
                event_id=event["id"],
                calendar_id=calendar_id,
                summary=event.get("summary"),
                description=event.get("description"),
                status=event.get("status"),
                start_time=_parse_event_datetime(event.get("start")),
                end_time=_parse_event_datetime(event.get("end")),
                organizer_email=(event.get("organizer") or {}).get("email"),
                created_at=_parse_iso_datetime(event.get("created")),
                updated_at=_parse_iso_datetime(event.get("updated")),
                is_deleted=(change_type == CHANGE_TYPE_CANCELLED),
            )
        )

        counts[change_type] = counts.get(change_type, 0) + 1

    return counts


def _parse_event_datetime(node: dict[str, Any] | None) -> datetime | None:
    if not node:
        return None
    if "dateTime" in node:
        return datetime.fromisoformat(node["dateTime"])
    if "date" in node:
        return datetime.fromisoformat(node["date"])
    return None


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    # Google API는 'Z' suffix 사용 (예: '2026-05-15T10:00:00.000Z')
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
