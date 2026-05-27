from __future__ import annotations

from app.common.kafka.producer import CommonKafkaProducer
from app.monitoring_google_workspace_logs.services.collectors.sources.calendar_google_api import (
    CalendarChange,
)


CALENDAR_EVENTS_TOPIC = "google.calendar.events.raw"


def write_changes_to_kafka(
    changes: list[CalendarChange],
    topic: str = CALENDAR_EVENTS_TOPIC,
) -> int:
    """
    변경 이벤트들을 Kafka topic에 발행한다.

    각 메시지에 'change_type' 필드가 추가되어 발행되므로,
    Consumer가 added/modified/cancelled 분류 로직을 다시 만들 필요가 없다.

    Returns:
        발행 건수.
    """
    producer = CommonKafkaProducer()

    try:
        for change in changes:
            producer.send(
                topic=topic,
                key=change.event["id"],
                value={
                    "calendar_id": change.calendar_id,
                    "change_type": change.change_type,
                    "event": change.event,
                },
            )
        producer.flush()
        return len(changes)
    finally:
        producer.close()
