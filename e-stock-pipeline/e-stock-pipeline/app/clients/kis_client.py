import os
import json
from datetime import datetime, timedelta, timezone

import requests
from airflow.models import Variable


KST = timezone(timedelta(hours=9))


class KisClient:
    """
    한국투자증권 KIS Open API Client.

    역할:
    - 접근토큰 발급 및 캐싱
    - 국내주식 현재가 API 호출
    """

    def __init__(self):
        self.app_key = os.getenv("KIS_APP_KEY")
        self.app_secret = os.getenv("KIS_APP_SECRET")
        self.base_url = os.getenv(
            "KIS_BASE_URL",
            "https://openapi.koreainvestment.com:9443",
        )

        if not self.app_key or not self.app_secret:
            raise ValueError("KIS_APP_KEY 또는 KIS_APP_SECRET이 .env에 없습니다.")

    def get_access_token(self) -> str:
        """
        한국투자증권 접근토큰 발급.
        Airflow Variable에 캐싱해서 토큰 재사용.
        """
        cached = Variable.get("KIS_ACCESS_TOKEN_CACHE", default_var=None)

        if cached:
            cached_data = json.loads(cached)
            expires_at = datetime.fromisoformat(cached_data["expires_at"])

            if datetime.now(KST) < expires_at - timedelta(minutes=10):
                return cached_data["access_token"]

        url = f"{self.base_url}/oauth2/tokenP"

        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        response = requests.post(
            url,
            headers={"content-type": "application/json"},
            data=json.dumps(payload),
            timeout=10,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"토큰 발급 실패: {response.status_code}, {response.text}"
            )

        data = response.json()
        access_token = data["access_token"]

        expires_in = int(data.get("expires_in", 23 * 60 * 60))
        expires_at = datetime.now(KST) + timedelta(seconds=expires_in)

        Variable.set(
            "KIS_ACCESS_TOKEN_CACHE",
            json.dumps(
                {
                    "access_token": access_token,
                    "expires_at": expires_at.isoformat(),
                },
                ensure_ascii=False,
            ),
        )

        return access_token

    def get_current_price(self, stock_code: str) -> dict:
        """
        국내주식 현재가 조회.
        """
        access_token = self.get_access_token()

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100",
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
        }

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"KIS 현재가 API 호출 실패: {response.status_code}, {response.text}"
            )

        data = response.json()

        if data.get("rt_cd") != "0":
            raise RuntimeError(f"KIS API 응답 오류: {data}")

        return data