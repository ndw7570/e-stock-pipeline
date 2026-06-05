from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.common.db_core import session_scope
from app.monitoring_google_workspace_logs.services.database.model.calendar_sync_state import (
    CalendarSyncState,
)


class CalendarSyncStateService:
    """
    캘린더별 sync_token 영구 저장 서비스.

    사용 흐름:
    - get_sync_token(cal_id): 저장된 토큰 조회. 없으면 None → initial sync 필요
    - save_sync_token(cal_id, token): 새 nextSyncToken UPSERT
    - clear_sync_token(cal_id): 410 Gone 발생 시 토큰 폐기 → 다음에 initial sync 다시
    """

    @classmethod
    def get_sync_token(cls, calendar_id: str) -> str | None:
        with session_scope() as s:
            state = s.execute(
                select(CalendarSyncState).where(
                    CalendarSyncState.calendar_id == calendar_id
                )
            ).scalar_one_or_none()
            return state.sync_token if state else None

    @classmethod
    def save_sync_token(cls, calendar_id: str, sync_token: str) -> None:
        now = datetime.now(timezone.utc)
        with session_scope() as s:
            stmt = pg_insert(CalendarSyncState).values(
                calendar_id=calendar_id,
                sync_token=sync_token,
                last_synced_at=now,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["calendar_id"],
                set_={
                    "sync_token": stmt.excluded.sync_token,
                    "last_synced_at": stmt.excluded.last_synced_at,
                },
            )
            s.execute(stmt)

    @classmethod
    def clear_sync_token(cls, calendar_id: str) -> None:
        with session_scope() as s:
            s.execute(
                delete(CalendarSyncState).where(
                    CalendarSyncState.calendar_id == calendar_id
                )
            )