from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from app.monitoring_google_workspace_logs.services.collectors.orchestrate_consume import (
    consume_to_database,
)


default_args = {
    "owner": "data-eng",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="google_calendar_kafka_to_db",
    description="Kafka → PostgreSQL 적재 (Consumer)",
    default_args=default_args,
    start_date=datetime(2026, 5, 1),
    schedule="*/5 * * * *",
    catchup=False,
    tags=["google", "calendar", "consumer"],
) as dag:
    PythonOperator(
        task_id="consume_kafka_to_db",
        python_callable=consume_to_database,
    )
