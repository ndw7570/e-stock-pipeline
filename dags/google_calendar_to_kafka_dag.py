from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from app.monitoring_google_workspace_logs.services.collectors.orchestrate_sync import (
    sync_all_calendars,
)


default_args = {
    "owner": "data-eng",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="google_calendar_to_kafka",
    description="Google Calendar 변경 → Kafka 발행 (Producer)",
    default_args=default_args,
    start_date=datetime(2026, 5, 1),
    schedule="*/5 * * * *",
    catchup=False,
    tags=["google", "calendar", "producer"],
) as dag:
    PythonOperator(
        task_id="sync_calendars_to_kafka",
        python_callable=sync_all_calendars,
    )