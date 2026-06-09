from app.estock.clients.kis_client import KisClient
from app.estock.repositories.stock_price_repository import StockCurrentPriceRepository, StockOhlcvRepository

def collect_kis_current_price(stock_code: str, stock_name: str):
    """
    KIS 현재가 수집 전체 흐름.

    1. KIS API 호출
    2. 응답 검증
    3. PostgreSQL 저장
    """
    client = KisClient()
    repository = StockCurrentPriceRepository()

    api_response = client.get_current_price(stock_code)
    repository.insert_current_price(
        stock_code=stock_code,
        stock_name=stock_name,
        api_response=api_response,
    )

    output = api_response.get("output", {})
    current_price = output.get("stck_prpr")

    print(f"[SUCCESS] {stock_name}({stock_code}) 현재가 저장 완료: {current_price}")


def collect_kis_period_price(
    stock_code: str,
    stock_name: str,
    start_date: str = "20260101",
    end_date: str = "20261231",
    period_code: str = "D",
):
    """
    KIS 일/주/월/년 OHLCV 수집 후 PostgreSQL 저장.

    period_code:
    - D: 일봉
    - W: 주봉
    - M: 월봉
    - Y: 년봉
    """
    client = KisClient()
    repository = StockOhlcvRepository()

    api_response = client.get_period_price(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        period_code=period_code,
        adjusted_price="0",
    )

    saved_count = repository.upsert_period_prices(
        stock_code=stock_code,
        stock_name=stock_name,
        period_code=period_code,
        api_response=api_response,
    )

    print(
        f"[SUCCESS] {stock_name}({stock_code}) "
        f"{period_code} OHLCV 저장 완료: {saved_count}건"
    )