from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from googleapiclient.errors import HttpError

from app.monitoring_google_workspace_logs.clients.google_calendar_client import (
    GoogleCalendarClient,
)
from app.monitoring_google_workspace_logs.services.database.handle_calendar_sync_state import (
    CalendarSyncStateService,
)
from app.monitoring_google_workspace_logs.services.database.model.calendar_event_changelog import (
    CHANGE_TYPE_ADDED,
    CHANGE_TYPE_CANCELLED,
    CHANGE_TYPE_MODIFIED,
)


@dataclass
class CalendarChange:
    """
    Source가 fetch한 변경 이벤트의 표준 단위.

    각 Sink(DB / Kafka / 미래의 Slack 등)는 이 객체를 받아
    자기 방식대로 저장/발행한다. Sink는 Google API dict의 모양을 직접 몰라도 됨.
    """

    event: dict[str, Any]
    calendar_id: str
    change_type: str


def fetch_all_calendar_changes() -> tuple[list[CalendarChange], dict[str, str]]:
    """
    접근 가능한 모든 캘린더의 변경 이벤트를 sync_token 기반 증분 수집한다.

    중요: sync_token은 여기서 저장하지 않고 new_tokens dict로만 반환한다.
    모든 Sink가 성공적으로 처리한 후에 commit_sync_tokens()로 영구 저장해야
    "토큰은 커밋됐는데 적재는 실패" 같은 데이터 손실을 방지할 수 있다.

    Returns:
        (changes, new_tokens)
        - changes: 변경 이벤트 리스트
        - new_tokens: {calendar_id: 새 sync_token} — commit 대기
    """
    client = GoogleCalendarClient()
    calendars = client.list_calendars()

    all_changes: list[CalendarChange] = []
    new_tokens: dict[str, str] = {}

    for cal in calendars:
        cal_id = cal["id"]
        try:
            cal_changes, next_token = _fetch_one_calendar(client, cal_id)
            all_changes.extend(cal_changes)
            if next_token:
                new_tokens[cal_id] = next_token
        except Exception as e:
            print(f"[ERROR] fetch failed for {cal_id}: {type(e).__name__}: {e}")

    return all_changes, new_tokens


def commit_sync_tokens(new_tokens: dict[str, str]) -> None:
    """
    모든 Sink가 성공 후 호출. sync_token을 영구 저장.
    이걸 호출해야 다음 sync 때 증분 수집이 동작한다.
    """
    for cal_id, token in new_tokens.items():
        CalendarSyncStateService.save_sync_token(cal_id, token)


def _fetch_one_calendar(
    client: GoogleCalendarClient,
    calendar_id: str,
) -> tuple[list[CalendarChange], str | None]:
    """단일 캘린더 fetch (sync_token 우선, 없으면 initial)."""
    sync_token = CalendarSyncStateService.get_sync_token(calendar_id)

    if sync_token:
        try:
            events, next_token = client.list_events_by_sync_token(
                sync_token=sync_token,
                calendar_id=calendar_id,
            )
            is_initial = False
        except HttpError as e:
            if e.resp.status == 410:
                print(f"[INFO] sync_token expired for {calendar_id}, resetting")
                CalendarSyncStateService.clear_sync_token(calendar_id)
                events, next_token = client.list_events_for_initial_sync(
                    calendar_id=calendar_id,
                )
                is_initial = True
            else:
                raise
    else:
        events, next_token = client.list_events_for_initial_sync(
            calendar_id=calendar_id,
        )
        is_initial = True

    changes = [
        CalendarChange(
            event=event,
            calendar_id=calendar_id,
            change_type=_classify_change(event, is_initial),
        )
        for event in events
    ]
    return changes, next_token


def _classify_change(event: dict[str, Any], is_initial_sync: bool) -> str:
    if event.get("status") == "cancelled":
        return CHANGE_TYPE_CANCELLED
    return CHANGE_TYPE_ADDED if is_initial_sync else CHANGE_TYPE_MODIFIED
