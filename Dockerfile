FROM apache/airflow:3.1.6-python3.12

USER airflow

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

# dbt-postgres + astronomer-cosmos (Airflow ↔ dbt 통합)
RUN pip install --no-cache-dir "astronomer-cosmos[dbt-postgres]>=1.6,<2.0"