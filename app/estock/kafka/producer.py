import json
import os

from kafka import KafkaProducer


def create_kafka_producer() -> KafkaProducer:
    """
    Kafka Producer 생성 공통 함수.
    """
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-1:29092")

    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        key_serializer=lambda key: key.encode("utf-8") if key else None,
        value_serializer=lambda value: json.dumps(
            value,
            ensure_ascii=False,
        ).encode("utf-8"),
        acks="all",
        retries=3,
    )