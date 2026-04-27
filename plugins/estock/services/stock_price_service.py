from estock.clients.kis_client import KisClient
from estock.repositories.stock_price_repository import StockPriceRepository


def collect_kis_current_price(stock_code: str, stock_name: str):
    """
    KIS 현재가 수집 전체 흐름.

    1. KIS API 호출
    2. 응답 검증
    3. PostgreSQL 저장
    """
    client = KisClient()
    repository = StockPriceRepository()

    api_response = client.get_current_price(stock_code)
    repository.insert_current_price(
        stock_code=stock_code,
        stock_name=stock_name,
        api_response=api_response,
    )

    output = api_response.get("output", {})
    current_price = output.get("stck_prpr")

    print(f"[SUCCESS] {stock_name}({stock_code}) 현재가 저장 완료: {current_price}")