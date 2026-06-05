from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, String, Text

from app.common.db_core import Base


@dataclass
class CalendarSyncStateModel:
    """캘린더별 동기화 상태 DTO."""

    calendar_id: str
    sync_token: Optional[str]
    last_synced_at: Optional[datetime]


class CalendarSyncState(Base):
    """
    캘린더별 sync_token 영구 저장 ORM.
    primary key = calendar_id (캘린더당 한 행).
    """

    __tablename__ = "calendar_sync_state"
    __table_args__ = {"schema": "google_workspace"}

    calendar_id = Column(String(200), primary_key=True)
    sync_token = Column(Text, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)


class CalendarSyncStateDict:
    """컬럼명 ↔ 한국어 라벨."""

    exposing_name = {
        "calendar_id": "캘린더ID",
        "sync_token": "동기화토큰",
        "last_synced_at": "마지막동기화시각",
    }