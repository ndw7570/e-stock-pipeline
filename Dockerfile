FROM apache/airflow:3.1.6-python3.12

USER airflow

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

# Drive RAG 도메인은 최신 API가 필요하므로 강제 override.
RUN pip install --no-cache-dir --upgrade "sentence-transformers>=3.0"
# dbt-postgres + astronomer-cosmos (Airflow ↔ dbt 통합)
# RUN pip install --no-cache-dir "astronomer-cosmos[dbt-postgres]>=1.6,<2.0"
RUN pip install --no-cache-dir "astronomer-cosmos[dbt-postgres]>=1.6,<2.0" "dbt-core>=1.8,<2.0" "dbt-postgres>=1.8,<2.0"
