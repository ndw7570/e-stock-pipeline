from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.common.db_core import Base


@dataclass
class CalendarEventModel:
    """
    Google Calendar 이벤트 DTO.
    수집/입력 단계에서 사용. ORM 객체로 변환되어 DB에 저장된다.
    """

    event_id: str
    calendar_id: str
    summary: Optional[str]
    description: Optional[str]
    status: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    organizer_email: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_deleted: Optional[bool] = False


class CalendarEvent(Base):
    """
    Google Calendar 이벤트 ORM 매핑.
    Google API의 event.id를 primary key로 사용 → 동일 이벤트의 UPSERT가 자연스러움.
    """

    __tablename__ = "calendar_event"
    __table_args__ = {"schema": "google_workspace"}

    event_id = Column(String(200), primary_key=True)
    calendar_id = Column(String(200), nullable=False)
    summary = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    organizer_email = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)


class CalendarEventDict:
    """
    컬럼명 ↔ 한국어 라벨 매핑.
    리포트/엑셀 export, UI 라벨링 등에서 사용.
    """

    exposing_name = {
        "event_id": "이벤트ID",
        "calendar_id": "캘린더ID",
        "summary": "제목",
        "description": "설명",
        "status": "상태",
        "start_time": "시작시각",
        "end_time": "종료시각",
        "organizer_email": "주최자이메일",
        "created_at": "생성일시",
        "updated_at": "수정일시",
        "is_deleted": "삭제여부",
    }
