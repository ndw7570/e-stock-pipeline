import json

from estock.kafka.consumer import create_kafka_consumer
from estock.kafka.topics import KIS_STOCK_TRADE_RAW
from estock.kafka.kis_message_classifier import classify_kis_raw_message


def main():
    consumer = create_kafka_consumer(
        topic=KIS_STOCK_TRADE_RAW,
        group_id="kis-trade-raw-debug-consumer",
        auto_offset_reset="earliest",
    )

    print(f"[DEBUG Consumer Start] topic={KIS_STOCK_TRADE_RAW}")

    for message in consumer:
        print("=" * 100)
        print(f"topic     : {message.topic}")
        print(f"partition : {message.partition}")
        print(f"offset    : {message.offset}")
        print(f"key       : {message.key}")

        value = message.value
        print("[value]")
        print(json.dumps(value, ensure_ascii=False, indent=2))

        raw_message = value.get("raw_message")
        message_type = classify_kis_raw_message(raw_message)

        print("[message_type]")
        print(message_type)

        print("[raw_message]")
        print(raw_message)

        consumer.commit()


if __name__ == "__main__":
    main()