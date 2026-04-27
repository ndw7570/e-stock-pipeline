from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from estock.services.stock_price_service import collect_kis_current_price


default_args = {
    "owner": "namubuntu",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


with DAG(
    dag_id="kis_current_price_to_postgres",
    description="한국투자증권 KIS API 현재가 조회 후 PostgreSQL 저장",
    default_args=default_args,
    start_date=datetime(2026, 4, 26),
    schedule="*/5 * * * *",
    catchup=False,
    tags=["kis", "stock", "api", "postgres"],
) as dag:

    fetch_samsung_price = PythonOperator(
        task_id="fetch_samsung_current_price",
        python_callable=collect_kis_current_price,
        op_kwargs={
            "stock_code": "005930",
            "stock_name": "삼성전자",
        },
    )