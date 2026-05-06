from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from estock.services.stock_price_service import collect_kis_period_price


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}


with DAG(
    dag_id="kis_period_price_to_postgres",
    description="한국투자증권 KIS API 기간별시세 조회 후 PostgreSQL 저장",
    default_args=default_args,
    start_date=datetime(2026, 4, 26),
    schedule="30 16 * * 1-5",
    catchup=False,
    tags=["kis", "stock", "ohlcv", "postgres"],
) as dag:

    fetch_samsung_daily_price = PythonOperator(
        task_id="fetch_samsung_daily_price",
        python_callable=collect_kis_period_price,
        op_kwargs={
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "start_date": "20260101",
            "end_date": "{{ ds_nodash }}",
            "period_code": "D",
        },
    )