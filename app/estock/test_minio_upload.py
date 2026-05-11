import os
from io import BytesIO
from datetime import datetime

from minio import Minio

# 실행방법: docker compose --env-file .env.dev exec airflow-scheduler python -m estock.test_minio_upload

def main():
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    bucket_name = os.getenv("MINIO_BUCKET", "stock-data")

    client = Minio(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=False,
    )

    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    now = datetime.now()
    object_name = f"test/minio-test-{now.strftime('%Y%m%d-%H%M%S')}.txt"

    text = f"MinIO upload test success: {now.isoformat()}"
    data = text.encode("utf-8")

    client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=BytesIO(data),
        length=len(data),
        content_type="text/plain",
    )

    print(f"[SUCCESS] uploaded: s3://{bucket_name}/{object_name}")


if __name__ == "__main__":
    main()