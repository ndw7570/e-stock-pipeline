from app.common.kafka.producer import CommonKafkaProducer
from app.monitoring_google_workspace_logs.clients.google_calendar_client import (
    GoogleCalendarClient,
)   


CALENDAR_EVENTS_TOPIC = "google.calendar.events.raw"


def collect_calendar_events_to_kafka(
        topic: str = CALENDAR_EVENTS_TOPIC,
) -> int:
    """
    Google Calendar 이벤트를 조회해서 Kafka 토픽에 발행한다.

    Returns:
        발행한 이벤트 수
    """
    client = GoogleCalendarClient()
    producer = CommonKafkaProducer()

    try: 
        events = client.list_events_by_time_range()

        for event in events:
            producer.send(
                topic=topic, 
                key=event.get("id"),
                value=event
            )
        
        producer.flush()
        return len(events)
    finally:
        producer.close()

# key=event.get("id") — 같은 이벤트(같은 id)는 같은 Kafka 파티션으로 가서 순서 보장
# value=event — Google 응답 dict를 raw 그대로 발행 (downstream에서 자유롭게 가공)
# try/finally로 producer 누수 방지