import json
import os

from kafka import KafkaConsumer


def create_kafka_consumer(
    topic: str,
    group_id: str,
    auto_offset_reset: str = "earliest",
) -> KafkaConsumer:
    """
    Kafka Consumer 생성 공통 함수.

    Parameters
    ----------
    topic : str
        구독할 Kafka topic 이름

    group_id : str
        Consumer group ID

    auto_offset_reset : str
        earliest 또는 latest
    """
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-1:29092")

    return KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        auto_offset_reset=auto_offset_reset,
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        key_deserializer=lambda key: key.decode("utf-8") if key else None,
    )