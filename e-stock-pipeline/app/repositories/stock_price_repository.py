import os
import json

import psycopg2
from airflow.hooks.base import BaseHook


class StockPriceRepository:
    """
    주식 현재가 저장소.

    역할:
    - PostgreSQL 연결
    - 테이블 생성
    - 현재가 데이터 저장
    """

    def __init__(self):
        self.conn_info = self._load_conn_info()

    def _load_conn_info(self) -> dict:
        """
        PostgreSQL 접속 정보 로드.

        우선순위:
        1. Airflow Connection: stock_postgres
        2. 기존 환경변수 방식 fallback
        """
        try:
            conn = BaseHook.get_connection("stock_postgres")

            return {
                "host": conn.host,
                "port": conn.port or 5432,
                "dbname": conn.schema,
                "user": conn.login,
                "password": conn.password,
            }

        except Exception:
            return {
                "host": os.getenv("STOCK_DB_HOST", "postgres"),
                "port": os.getenv("STOCK_DB_PORT", "5432"),
                "dbname": os.getenv("STOCK_DB_NAME", "stock_db"),
                "user": os.getenv("STOCK_DB_USER", os.getenv("POSTGRES_USER", "airflow")),
                "password": os.getenv(
                    "STOCK_DB_PASSWORD",
                    os.getenv("POSTGRES_PASSWORD", "airflow"),
                ),
            }

    def _connect(self):
        return psycopg2.connect(**self.conn_info)

    def create_table_if_not_exists(self):
        conn = self._connect()

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS kis_domestic_stock_price (
                            id BIGSERIAL PRIMARY KEY,
                            stock_code VARCHAR(20) NOT NULL,
                            stock_name VARCHAR(100),
                            current_price NUMERIC,
                            price_change NUMERIC,
                            change_rate NUMERIC,
                            accumulated_volume BIGINT,
                            raw_json JSONB NOT NULL,
                            collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        );
                        """
                    )
        finally:
            conn.close()

    def insert_current_price(
        self,
        stock_code: str,
        stock_name: str,
        api_response: dict,
    ):
        self.create_table_if_not_exists()

        output = api_response.get("output", {})

        current_price = output.get("stck_prpr")
        price_change = output.get("prdy_vrss")
        change_rate = output.get("prdy_ctrt")
        accumulated_volume = output.get("acml_vol")

        conn = self._connect()

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO kis_domestic_stock_price (
                            stock_code,
                            stock_name,
                            current_price,
                            price_change,
                            change_rate,
                            accumulated_volume,
                            raw_json,
                            collected_at
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s::jsonb, NOW()
                        );
                        """,
                        (
                            stock_code,
                            stock_name,
                            int(current_price) if current_price else None,
                            int(price_change) if price_change else None,
                            float(change_rate) if change_rate else None,
                            int(accumulated_volume) if accumulated_volume else None,
                            json.dumps(api_response, ensure_ascii=False),
                        ),
                    )
        finally:
            conn.close()