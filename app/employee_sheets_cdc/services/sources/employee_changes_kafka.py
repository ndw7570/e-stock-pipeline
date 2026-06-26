"""
Debezium이 publish하는 직원 변경 이벤트를 Kafka에서 consume.

[메커니즘]
- Topic: dbz.interx_hr.employee
- Format: JSON (Debezium 표준, schemas.enable=false)
- Group ID: 한 Consumer 그룹 = 메시지 1번만 (중복 방지)

[Commit 전략]
- enable_auto_commit=False — 처리 끝나야 commit
- 처리 중 죽으면 같은 메시지 재전송 → at-least-once 보장
- Sheets API 호출 실패 시도 메시지 안 잃음
"""
from __future__ import annotations

import json
from typing import Any, Iterator

from kafka import KafkaConsumer

from app.common.config.settings import settings


TOPIC = "dbz.interx_hr.employee"
DEFAULT_GROUP_ID = "employee-sheets-cdc"


def consume_employee_changes(
    group_id: str = DEFAULT_GROUP_ID,
    auto_offset_reset: str = "earliest",
) -> Iterator[dict[str, Any]]:
    """
    Kafka에서 Debezium 메시지를 받아 dict로 yield.

    Args:
        group_id: Consumer 그룹 ID.
                  - 같은 group_id 여러 인스턴스 = 메시지 분산
                  - 다른 group_id = 처음부터 다시 받음 (검증용)
        auto_offset_reset:
                  - "earliest": 토픽 처음부터 (snapshot 포함)
                  - "latest": 새 메시지만

    Yields:
        {
            "key": str | None,      # Debezium key (employee_id 등)
            "value": dict | None,   # Debezium payload (op, before, after, source)
            "topic": str,
            "partition": int,
            "offset": int,
        }

    [commit 시점]
    yield 후 호출자가 처리 끝나면 commit. 처리 중 예외 시 다음 cycle에서 재시도.
    """
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=settings.kafka.bootstrap_servers,
        group_id=group_id,
        auto_offset_reset=auto_offset_reset,
        enable_auto_commit=False,
        # JSON 디시리얼라이저
        value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
    )

    try:
        for msg in consumer:
            yield {
                "key": msg.key,
                "value": msg.value,
                "topic": msg.topic,
                "partition": msg.partition,
                "offset": msg.offset,
            }
            consumer.commit()  # 처리 완료 후 commit
    finally:
        consumer.close()
