from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from cosmos import DbtTaskGroup, ProfileConfig, ProjectConfig
from cosmos.profiles import PostgresUserPasswordProfileMapping

from app.monitoring_google_workspace_logs.services.collectors.orchestrate_consume import (
    consume_to_database,
)


# ── cosmos 설정 ──────────────────────────────────────
DBT_PROJECT_PATH = "/opt/airflow/dbt"

profile_config = ProfileConfig(
    profile_name="e_stock_pipeline",        # dbt_project.yml의 profile 이름
    target_name="dev",                       # profiles.yml의 target
    profile_mapping=PostgresUserPasswordProfileMapping(
        conn_id="dbt_postgres",              # docker-compose의 AIRFLOW_CONN_DBT_POSTGRES
        profile_args={"schema": "dbt_default"},
    ),
)
# ─────────────────────────────────────────────────────


default_args = {
    "owner": "data-eng",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="google_calendar_kafka_to_db",
    description="Kafka → DB 적재 + dbt 모델 자동 빌드 (cosmos)",
    default_args=default_args,
    start_date=datetime(2026, 5, 1),
    schedule="*/5 * * * *",
    catchup=False,
    tags=["google", "calendar", "consumer", "dbt", "cosmos"],
) as dag:

    consume = PythonOperator(
        task_id="consume_kafka_to_db",
        python_callable=consume_to_database,
    )

    # dbt 모델 6개를 자동으로 task로 변환 — cosmos의 마법
    dbt_models = DbtTaskGroup(
        group_id="dbt_models",
        project_config=ProjectConfig(DBT_PROJECT_PATH),
        profile_config=profile_config,
    )

    consume >> dbt_models       # Consumer 끝나면 dbt 모델들 차례로 빌드
