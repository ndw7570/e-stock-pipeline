from __future__ import annotations

from app.monitoring_google_workspace_logs.services.collectors.sinks.calendar_database import (
    write_changes_to_database,
)
from app.monitoring_google_workspace_logs.services.collectors.sinks.calendar_kafka import (
    write_changes_to_kafka,
)
from app.monitoring_google_workspace_logs.services.collectors.sources.calendar_google_api import (
    commit_sync_tokens,
    fetch_all_calendar_changes,
)


def sync_all_calendars() -> dict[str, object]:
    """
    오케스트레이터:
        1) Source에서 변경 이벤트 fetch (모든 캘린더 × sync_token 증분)
        2) 모든 Sink에 분배 (DB + Kafka)
        3) 모두 성공 시 sync_token commit (다음 호출 시 증분 보장)

    중요한 설계 결정:
        sync_token commit은 마지막에 한 번만. 도중에 실패하면 sync_token이
        커밋 안 되니, 다음 호출 때 같은 데이터를 다시 fetch 가능 (at-least-once).

    Returns:
        {
            'total': 전체 변경 수,
            'db': {added: n, modified: n, cancelled: n},
            'kafka': 발행 건수,
            'committed_tokens': 토큰 커밋된 캘린더 수,
        }
    """
    # 1) fetch
    changes, new_tokens = fetch_all_calendar_changes()

    # 2) sinks — 양쪽으로 분배
    db_stats = write_changes_to_database(changes)
    kafka_count = write_changes_to_kafka(changes)

    # 3) 모든 sink 성공 후에만 sync_token commit
    commit_sync_tokens(new_tokens)

    return {
        "total": len(changes),
        "db": db_stats,
        "kafka": kafka_count,
        "committed_tokens": len(new_tokens),
    }
