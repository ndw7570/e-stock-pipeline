import json
from typing import Any

from kafka import KafkaProducer

from app.common.config.settings import settings


class CommonKafkaProducer:
    """
    프로젝트 공통 Kafka Producer.

    역할:
    - Kafka 연결 설정 공통화
    - dict 메시지를 JSON으로 직렬화
    - topic에 메시지 발행
    - key가 있는 경우 key 기반 파티셔닝 가능

    사용 예:
        producer = CommonKafkaProducer()
        producer.send(
            topic="google.calendar.events.raw",
            value={"event_id": "abc", "summary": "회의"},
            key="abc",
        )
        producer.close()
    """

    def __init__(self) -> None:
        self.producer = KafkaProducer(
            bootstrap_servers=settings.kafka.bootstrap_servers,
            client_id=settings.kafka.client_id,
            key_serializer=self._serialize_key,
            value_serializer=self._serialize_value,
            acks="all",
            retries=3,
        )

    @staticmethod
    def _serialize_key(key: str | None) -> bytes | None:
        if key is None:
            return None

        return key.encode("utf-8")

    @staticmethod
    def _serialize_value(value: dict[str, Any]) -> bytes:
        return json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")


    def send(
        self,
        topic: str,
        value: dict[str, Any],
        key: str | None = None,
    ) -> None:
        """
        Kafka topic에 메시지를 발행한다.

        Args:
            topic: Kafka topic 이름
            value: JSON 직렬화 가능한 dict 메시지
            key: Kafka message key. 같은 key는 같은 파티션으로 갈 가능성이 높음.
        """
        future = self.producer.send(
            topic=topic,
            key=key,
            value=value,
        )

        # 전송 실패를 조기에 확인하기 위해 get() 호출
        future.get(timeout=10)

    def flush(self) -> None:
        """
        버퍼에 남아 있는 메시지를 Kafka로 밀어넣는다.
        """
        self.producer.flush()

    def close(self) -> None:
        """
        Producer 연결 종료.
        """
        self.producer.flush()
        self.producer.close()