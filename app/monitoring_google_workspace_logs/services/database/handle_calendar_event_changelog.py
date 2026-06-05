from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Optional

from sqlalchemy import desc, select

from app.common.db_core import session_scope
from app.monitoring_google_workspace_logs.services.database.model.calendar_event_changelog import (
    CalendarEventChangelog,
    CalendarEventChangelogModel,
)


class CalendarEventChangelogService:
    """
    변경 이력 append-only 서비스.

    insert_change: 한 행 INSERT
    list_changes_for_event: 특정 이벤트의 이력 시간순
    list_recent_changes: 최근 변경 이력 N건
    """

    @classmethod
    def insert_change(cls, model: CalendarEventChangelogModel) -> int:
        """
        변경 이력 한 행 INSERT.

        Returns:
            새로 생성된 행의 id.
        """
        with session_scope() as s:
            row = CalendarEventChangelog(**asdict(model))
            s.add(row)
            s.flush()
            return row.id

    @classmethod
    def list_changes_for_event(
        cls,
        event_id: str,
        limit: int = 100,
    ) -> list[CalendarEventChangelog]:
        """특정 이벤트의 변경 이력. 오래된 순."""
        with session_scope() as s:
            result = s.execute(
                select(CalendarEventChangelog)
                .where(CalendarEventChangelog.event_id == event_id)
                .order_by(CalendarEventChangelog.observed_at)
                .limit(limit)
            )
            return list(result.scalars())

    @classmethod
    def list_recent_changes(
        cls,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[CalendarEventChangelog]:
        """최근 변경 이력. 최신 순."""
        with session_scope() as s:
            stmt = select(CalendarEventChangelog).order_by(
                desc(CalendarEventChangelog.observed_at)
            )
            if since is not None:
                stmt = stmt.where(CalendarEventChangelog.observed_at >= since)
            result = s.execute(stmt.limit(limit))
            return list(result.scalars())