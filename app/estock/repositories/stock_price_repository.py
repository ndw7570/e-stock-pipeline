import os
import json
from datetime import datetime
import psycopg2
from airflow.hooks.base import BaseHook

class StockCurrentPriceRepository:
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


class StockOhlcvRepository:
    """
    주식 OHLCV 저장소.

    역할:
    - PostgreSQL 연결
    - 테이블 생성
    - 국내주식기간별시세(일/주/월/년) 데이터 저장
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
                        CREATE TABLE IF NOT EXISTS kis_domestic_stock_ohlcv (
                            id BIGSERIAL PRIMARY KEY,
                            stock_code VARCHAR(20) NOT NULL,
                            stock_name VARCHAR(100),
                            period_code VARCHAR(1) NOT NULL,
                            trade_date DATE NOT NULL,
                            open_price NUMERIC,
                            high_price NUMERIC,
                            low_price NUMERIC,
                            close_price NUMERIC,
                            accumulated_volume BIGINT,
                            accumulated_trading_value NUMERIC,
                            raw_json JSONB NOT NULL,
                            collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

                            CONSTRAINT uq_kis_domestic_stock_ohlcv
                                UNIQUE (stock_code, period_code, trade_date)
                        );
                        """
                    )
        finally:
            conn.close()

    def upsert_period_prices(
        self,
        stock_code: str,
        stock_name: str,
        period_code: str,
        api_response: dict,
    ) -> int:
        """
        KIS 국내주식기간별시세 API 응답을 OHLCV 테이블에 저장.

        period_code:
        - D: 일봉
        - W: 주봉
        - M: 월봉
        - Y: 년봉
        """
        self.create_table_if_not_exists()

        rows = api_response.get("output2", [])

        if not rows:
            return 0

        conn = self._connect()

        saved_count = 0

        try:
            with conn:
                with conn.cursor() as cur:
                    for item in rows:
                        trade_date = item.get("stck_bsop_date")

                        if not trade_date:
                            continue

                        cur.execute(
                            """
                            INSERT INTO kis_domestic_stock_ohlcv (
                                stock_code,
                                stock_name,
                                period_code,
                                trade_date,
                                open_price,
                                high_price,
                                low_price,
                                close_price,
                                accumulated_volume,
                                accumulated_trading_value,
                                raw_json,
                                collected_at,
                                updated_at
                            )
                            VALUES (
                                %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s,
                                %s::jsonb,
                                NOW(),
                                NOW()
                            )
                            ON CONFLICT (stock_code, period_code, trade_date)
                            DO UPDATE SET
                                stock_name = EXCLUDED.stock_name,
                                open_price = EXCLUDED.open_price,
                                high_price = EXCLUDED.high_price,
                                low_price = EXCLUDED.low_price,
                                close_price = EXCLUDED.close_price,
                                accumulated_volume = EXCLUDED.accumulated_volume,
                                accumulated_trading_value = EXCLUDED.accumulated_trading_value,
                                raw_json = EXCLUDED.raw_json,
                                updated_at = NOW();
                            """,
                            (
                                stock_code,
                                stock_name,
                                period_code,
                                self._to_date(trade_date),
                                self._to_int(item.get("stck_oprc")),
                                self._to_int(item.get("stck_hgpr")),
                                self._to_int(item.get("stck_lwpr")),
                                self._to_int(item.get("stck_clpr")),
                                self._to_int(item.get("acml_vol")),
                                self._to_int(item.get("acml_tr_pbmn")),
                                json.dumps(item, ensure_ascii=False),
                            ),
                        )

                        saved_count += 1

        finally:
            conn.close()

        return saved_count

    def _to_int(self, value):
        if value in (None, ""):
            return None

        try:
            return int(value)
        except ValueError:
            return None

    def _to_float(self, value):
        if value in (None, ""):
            return None

        try:
            return float(value)
        except ValueError:
            return None

    def _to_date(self, value: str):
        """
        YYYYMMDD 문자열을 DATE로 변환.
        """
        if not value:
            return None

        return datetime.strptime(value, "%Y%m%d").date()