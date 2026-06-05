from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, Column, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB

from app.common.db_core import Base


# 변경 타입 상수 (서비스에서 import해서 사용)
CHANGE_TYPE_ADDED = "added"
CHANGE_TYPE_MODIFIED = "modified"
CHANGE_TYPE_CANCELLED = "cancelled"


@dataclass
class CalendarEventChangelogModel:
    """변경 이력 DTO (입력용)."""

    event_id: str
    calendar_id: str
    change_type: str  # 'added' / 'modified' / 'cancelled'
    event_summary: Optional[str]
    event_status: Optional[str]
    event_start_time: Optional[datetime]
    event_end_time: Optional[datetime]
    raw_payload: dict[str, Any]


class CalendarEventChangelog(Base):
    """
    Calendar 이벤트 변경 이력 (append-only).
    같은 event_id에 대해 여러 행이 시간순으로 쌓인다.
    """

    __tablename__ = "calendar_event_changelog"
    __table_args__ = (
        Index("ix_changelog_event_id", "event_id"),
        Index("ix_changelog_observed_at", "observed_at"),
        {"schema": "google_workspace"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(String(200), nullable=False)
    calendar_id = Column(String(200), nullable=False)
    change_type = Column(String(20), nullable=False)
    event_summary = Column(String(500), nullable=True)
    event_status = Column(String(20), nullable=True)
    event_start_time = Column(DateTime(timezone=True), nullable=True)
    event_end_time = Column(DateTime(timezone=True), nullable=True)
    raw_payload = Column(JSONB, nullable=False)
    observed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CalendarEventChangelogDict:
    exposing_name = {
        "id": "이력ID",
        "event_id": "이벤트ID",
        "calendar_id": "캘린더ID",
        "change_type": "변경구분",
        "event_summary": "제목",
        "event_status": "상태",
        "event_start_time": "시작시각",
        "event_end_time": "종료시각",
        "raw_payload": "원본JSON",
        "observed_at": "관찰시각",
    }