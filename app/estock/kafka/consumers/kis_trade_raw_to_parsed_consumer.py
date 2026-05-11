from estock.kafka.consumer import create_kafka_consumer
from estock.kafka.producer import create_kafka_producer
from estock.kafka.kis_message_classifier import classify_kis_raw_message
from estock.kafka.kis_trade_parser import parse_kis_trade_raw_message
from estock.kafka.topics import (
    KIS_STOCK_TRADE_RAW,
    KIS_STOCK_TRADE_PARSED,
)


def main():
    consumer = create_kafka_consumer(
        topic=KIS_STOCK_TRADE_RAW,
        group_id="kis-trade-raw-to-parsed-consumer",
        auto_offset_reset="earliest",
    )

    producer = create_kafka_producer()

    print("[START] KIS trade raw → parsed consumer")
    print(f"[SOURCE TOPIC] {KIS_STOCK_TRADE_RAW}")
    print(f"[TARGET TOPIC] {KIS_STOCK_TRADE_PARSED}")

    for message in consumer:
        value = message.value

        raw_message = value.get("raw_message")
        message_type = classify_kis_raw_message(raw_message)

        if message_type != "trade":
            print(
                f"[SKIP] offset={message.offset}, "
                f"message_type={message_type}"
            )
            consumer.commit()
            continue

        try:
            parsed_event = parse_kis_trade_raw_message(raw_message)

            parsed_event["received_at"] = value.get("received_at")
            parsed_event["kafka_raw_offset"] = message.offset
            parsed_event["kafka_raw_partition"] = message.partition

            producer.send(
                KIS_STOCK_TRADE_PARSED,
                key=parsed_event.get("stock_code"),
                value=parsed_event,
            )

            producer.flush()
            consumer.commit()

            print(
                f"[PARSED] stock_code={parsed_event.get('stock_code')}, "
                f"raw_offset={message.offset}"
            )

        except Exception as e:
            print(
                f"[ERROR] raw_offset={message.offset}, "
                f"error={e}, "
                f"raw_message={raw_message}"
            )

            # 지금 단계에서는 에러 메시지도 일단 commit해서 무한 반복을 막는다.
            # 나중에는 kis.stock.trade.error 토픽으로 보내는 구조가 더 좋다.
            consumer.commit()


if __name__ == "__main__":
    main()