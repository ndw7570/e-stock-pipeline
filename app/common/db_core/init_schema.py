"""
프로젝트 도메인 스키마/테이블 초기화 진입점.
airflow-init 컨테이너가 호출하여 새 환경에서도 자동 셋업.

새 도메인 모델 추가 시:
  1. 아래 import 블록에 모델 import 한 줄 추가
  2. 필요하면 CREATE SCHEMA 줄 추가
재실행은 idempotent (IF NOT EXISTS + create_all은 기존 테이블 건드리지 않음).
"""
from __future__ import annotations

from sqlalchemy import text

from app.common.db_core import Base, get_engine, session_scope

# === 도메인 모델 import (Base에 등록되게 — 빠뜨리면 그 테이블이 안 만들어짐) ===
from app.monitoring_google_workspace_logs.services.database.model.calendar_event import (  # noqa: F401
    CalendarEvent,
)
from app.monitoring_google_workspace_logs.services.database.model.calendar_event_changelog import (  # noqa: F401
    CalendarEventChangelog,
)
from app.monitoring_google_workspace_logs.services.database.model.calendar_sync_state import (  # noqa: F401
    CalendarSyncState,
)


SCHEMAS_TO_ENSURE = [
    "google_workspace",
    # 미래: "kis_stock", "slack" 등 도메인 추가 시 여기 추가
]


def main() -> None:
    # 1) 스키마 보장
    with session_scope() as s:
        for schema in SCHEMAS_TO_ENSURE:
            s.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            print(f"schema ensured: {schema}")

    # 2) Base에 등록된 모든 테이블 생성 (이미 있으면 skip)
    Base.metadata.create_all(get_engine())
    print("all tables created (idempotent)")


if __name__ == "__main__":
    main()
