from estock.kafka.consumer import create_kafka_consumer
from estock.kafka.topics import TEST_STOCK_PRICES


def main():
    consumer = create_kafka_consumer(
        topic=TEST_STOCK_PRICES,
        group_id="test-kafka-consumer",
        auto_offset_reset="earliest",
    )

    print(f"[Consumer Start] topic={TEST_STOCK_PRICES}")

    for message in consumer:
        print("=" * 80)
        print(f"topic     : {message.topic}")
        print(f"partition : {message.partition}")
        print(f"offset    : {message.offset}")
        print(f"key       : {message.key}")
        print(f"value     : {message.value}")

        consumer.commit()


if __name__ == "__main__":
    main()