import json
import os
import time
from datetime import datetime, timedelta, timezone

from estock.kafka.consumer import create_kafka_consumer
from estock.kafka.topics import TEST_STOCK_PRICES
from estock.storage.minio_storage import (
    create_minio_client,
    ensure_bucket,
    upload_text,
)


KST = timezone(timedelta(hours=9))


def main():
    # 지금은 테스트 Producer 메시지를 MinIO로 저장하는 단계
    topic = os.getenv("KAFKA_SOURCE_TOPIC", TEST_STOCK_PRICES)
    bucket_name = os.getenv("MINIO_BUCKET", "stock-data")

    consumer = create_kafka_consumer(
        topic=topic,
        group_id="kis-trade-minio-consumer",
        auto_offset_reset="earliest",
    )

    minio_client = create_minio_client()
    ensure_bucket(minio_client, bucket_name)

    buffer = []
    last_flush_time = time.time()

    print("[START] Kafka → MinIO Consumer")
    print(f"[INFO] topic={topic}")
    print(f"[INFO] bucket={bucket_name}")

    for message in consumer:
        buffer.append(message.value)

        should_flush_by_count = len(buffer) >= 5
        should_flush_by_time = time.time() - last_flush_time >= 10

        if not should_flush_by_count and not should_flush_by_time:
            continue

        now = datetime.now(KST)

        object_name = (
            f"raw/kis/trade/"
            f"dt={now.strftime('%Y-%m-%d')}/"
            f"hour={now.strftime('%H')}/"
            f"kafka-trade-{now.strftime('%Y%m%d-%H%M%S')}.jsonl"
        )

        jsonl_text = "\n".join(
            json.dumps(row, ensure_ascii=False)
            for row in buffer
        )

        upload_text(
            client=minio_client,
            bucket_name=bucket_name,
            object_name=object_name,
            text=jsonl_text,
            content_type="application/json",
        )

        consumer.commit()

        print(
            f"[SUCCESS] MinIO 저장 완료: "
            f"s3://{bucket_name}/{object_name}, rows={len(buffer)}"
        )

        buffer.clear()
        last_flush_time = time.time()


if __name__ == "__main__":
    main()