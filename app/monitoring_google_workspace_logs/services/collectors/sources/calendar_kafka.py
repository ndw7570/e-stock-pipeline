from __future__ import annotations

import json
from typing import Any, Iterator

from kafka import KafkaConsumer

from app.common.config.settings import settings


CALENDAR_EVENTS_TOPIC = "google.calendar.events.raw"


def consume_calendar_changes(
    group_id: str = "calendar-events-monitor",
    auto_offset_reset: str = "earliest",
    consumer_timeout_ms: int = 5000,
) -> Iterator[dict[str, Any]]:
    """
    Kafka topic 'google.calendar.events.raw'를 구독해 메시지를 yield한다.

    consumer_timeout_ms 동안 새 메시지가 없으면 자동 종료 (StopIteration) →
    batch 처리/학습용으로 적합. 무한 루프 안 함.

    Args:
        group_id:
            Consumer group ID. 같은 group을 가진 여러 consumer는 메시지를 분담함.
            다른 group은 같은 메시지를 독립적으로 다시 받음 (브로드캐스트).
        auto_offset_reset:
            'earliest' = 토픽 처음부터 (group이 처음 만들어질 때)
            'latest' = 새로 들어오는 메시지부터
        consumer_timeout_ms:
            poll 타임아웃. 이 시간 동안 새 메시지 없으면 종료.
            0 또는 음수면 무한 대기.

    Yields:
        Kafka 메시지의 value dict (이미 JSON 역직렬화된 상태).
        각 dict에는 Google Calendar event 필드들 + 'change_type' 포함.
    """
    consumer = KafkaConsumer(
        CALENDAR_EVENTS_TOPIC,
        bootstrap_servers=settings.kafka.bootstrap_servers,
        group_id=group_id,
        auto_offset_reset=auto_offset_reset,
        consumer_timeout_ms=consumer_timeout_ms,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda v: v.decode("utf-8") if v else None,
        enable_auto_commit=True,
    )

    try:
        for message in consumer:
            yield message.value
    finally:
        consumer.close()