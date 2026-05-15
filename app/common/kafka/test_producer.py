from app.common.kafka.producer import CommonKafkaProducer


def main() -> None:
    producer = CommonKafkaProducer()

    producer.send(
        topic="test.common.producer",
        key="test-key-1",
        value={
            "message": "hello kafka",
            "source": "common producer test",
        },
    )

    producer.close()

    print("Kafka message sent successfully.")


if __name__ == "__main__":
    main()