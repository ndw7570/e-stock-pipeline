from __future__ import annotations

from dataclasses import asdict

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.common.db_core import session_scope
from app.monitoring_google_workspace_logs.services.database.model.calendar_event import (
    CalendarEvent,
    CalendarEventModel,
)


class CalendarEventService:
    """
    Calendar 이벤트 CRUD 서비스.

    archive의 `handle_*_info.py` 패턴(classmethod 기반 CRUD 모음)을 그대로 따르되,
    - 예외 silently swallow 금지 → 그대로 raise (Airflow가 실패 감지 가능)
    - 세션은 task 단위 context manager로 (싱글톤 X, fork-safe)
    - PostgreSQL UPSERT는 `ON CONFLICT` 활용
    """

    @classmethod
    def fetch_all_events(cls) -> list[CalendarEvent]:
        """모든 이벤트 조회."""
        with session_scope() as s:
            result = s.execute(select(CalendarEvent))
            return list(result.scalars())

    @classmethod
    def get_event_by_id(cls, event_id: str) -> CalendarEvent | None:
        """단일 이벤트 조회. 없으면 None."""
        with session_scope() as s:
            return s.execute(
                select(CalendarEvent).where(CalendarEvent.event_id == event_id)
            ).scalar_one_or_none()

    @classmethod
    def add_event(cls, model: CalendarEventModel) -> None:
        """이벤트 한 건 INSERT. 같은 event_id가 이미 있으면 IntegrityError."""
        with session_scope() as s:
            s.add(CalendarEvent(**asdict(model)))

    @classmethod
    def update_event(cls, model: CalendarEventModel) -> int:
        """
        event_id 기준 UPDATE.

        Returns:
            영향받은 행 수. 0이면 해당 event_id 없음.
        """
        with session_scope() as s:
            stmt = (
                update(CalendarEvent)
                .where(CalendarEvent.event_id == model.event_id)
                .values(
                    calendar_id=model.calendar_id,
                    summary=model.summary,
                    description=model.description,
                    status=model.status,
                    start_time=model.start_time,
                    end_time=model.end_time,
                    organizer_email=model.organizer_email,
                    created_at=model.created_at,
                    updated_at=model.updated_at,
                    is_deleted=model.is_deleted,
                )
            )
            result = s.execute(stmt)
            return result.rowcount

    @classmethod
    def delete_event(cls, event_id: str) -> int:
        """
        하드 DELETE. soft delete가 필요하면 update_event로 is_deleted=True 처리.

        Returns:
            영향받은 행 수.
        """
        with session_scope() as s:
            result = s.execute(
                delete(CalendarEvent).where(CalendarEvent.event_id == event_id)
            )
            return result.rowcount

    @classmethod
    def upsert_event(cls, model: CalendarEventModel) -> None:
        """
        PostgreSQL UPSERT (INSERT ... ON CONFLICT DO UPDATE).
        Kafka consumer에서 이 메서드를 호출하면 멱등하게 적재 가능.
        """
        values = asdict(model)

        with session_scope() as s:
            stmt = pg_insert(CalendarEvent).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["event_id"],
                set_={
                    "calendar_id": stmt.excluded.calendar_id,
                    "summary": stmt.excluded.summary,
                    "description": stmt.excluded.description,
                    "status": stmt.excluded.status,
                    "start_time": stmt.excluded.start_time,
                    "end_time": stmt.excluded.end_time,
                    "organizer_email": stmt.excluded.organizer_email,
                    "created_at": stmt.excluded.created_at,
                    "updated_at": stmt.excluded.updated_at,
                    "is_deleted": stmt.excluded.is_deleted,
                },
            )
            s.execute(stmt)
