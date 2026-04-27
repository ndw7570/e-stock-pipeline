"""
간단한 Kafka producer 테스트.

실행: python producers/test_producer.py
"""

import json
import random
import time
from datetime import datetime, timezone

from kafka import KafkaProducer


# 호스트에서 실행 시: localhost:19092
# 컨테이너에서 실행 시: kafka-1:29092
#KAFKA_BOOTSTRAP = "kafka-1:29092"
KAFKA_BOOTSTRAP = "kafka-1:29092"
TOPIC_NAME = "test-stock-prices"

# 가짜 종목 리스트
TICKERS = [
    {"code": "005930", "name": "삼성전자", "base_price": 75000},
    {"code": "000660", "name": "SK하이닉스", "base_price": 180000},
    {"code": "035420", "name": "NAVER", "base_price": 200000},
]


def make_message(ticker: dict) -> dict:
    """가짜 시세 한 건 생성."""
    fluctuation = random.uniform(-0.02, 0.02)  # ±2%
    price = int(ticker["base_price"] * (1 + fluctuation))

    return {
        "ticker": ticker["code"],
        "name": ticker["name"],
        "price": price,
        "volume": random.randint(1_000, 100_000),
        "event_time": datetime.now(timezone.utc).isoformat(),
    }


def main():
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP],
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        # 종목 코드를 key 로 → 같은 종목은 같은 파티션에 가서 순서 보장
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )

    print(f"[producer] connected to {KAFKA_BOOTSTRAP}")
    print(f"[producer] sending to topic: {TOPIC_NAME}")
    print("[producer] Ctrl+C to stop")

    sent_count = 0
    try:
        while True:
            for ticker in TICKERS:
                msg = make_message(ticker)
                producer.send(TOPIC_NAME, key=ticker["code"], value=msg)
                sent_count += 1
                print(f"  [{sent_count}] {msg['name']}: {msg['price']:,}원 (vol={msg['volume']:,})")

            producer.flush()
            time.sleep(2)  # 2초마다 발행
    except KeyboardInterrupt:
        print(f"\n[producer] stopped. total sent: {sent_count}")
    finally:
        producer.close()


if __name__ == "__main__":
    main()