import json

from app.estock.kafka.consumer import create_kafka_consumer
from app.estock.kafka.topics import KIS_STOCK_TRADE_PARSED


def main():
    consumer = create_kafka_consumer(
        topic=KIS_STOCK_TRADE_PARSED,
        group_id="kis-trade-parsed-debug-consumer",
        auto_offset_reset="earliest",
    )

    print(f"[DEBUG Consumer Start] topic={KIS_STOCK_TRADE_PARSED}")

    for message in consumer:
        print("=" * 100)
        print(f"topic     : {message.topic}")
        print(f"partition : {message.partition}")
        print(f"offset    : {message.offset}")
        print(f"key       : {message.key}")
        print("[value]")
        print(json.dumps(message.value, ensure_ascii=False, indent=2))

        consumer.commit()


if __name__ == "__main__":
    main()