-- Airflow 메타DB 생성. 데이터 적재용 stock_db 는 POSTGRES_DB 환경변수로 자동 생성.
-- 비즈니스 테이블 (raw / cleaned / mart) 은 학습 진행하면서 단계적으로 추가.
CREATE DATABASE airflow_db;
