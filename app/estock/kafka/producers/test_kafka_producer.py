import time
from datetime import datetime, timedelta, timezone

from app.estock.kafka.producer import create_kafka_producer
from app.estock.kafka.topics import TEST_STOCK_PRICES


KST = timezone(timedelta(hours=9))


def main():
    producer = create_kafka_producer()

    for i in range(5):
        event = {
            "source": "test",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "price": 70000 + i,
            "event_time": datetime.now(KST).isoformat(),
        }

        producer.send(
            TEST_STOCK_PRICES,
            key=event["stock_code"],
            value=event,
        )

        producer.flush()

        print(f"[PRODUCED] {event}")

        time.sleep(1)

    producer.close()

    print("[SUCCESS] test messages produced")


if __name__ == "__main__":
    main()