import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from estock.clients.kis_client import KisClient
from estock.kafka.kis_message_classifier import classify_kis_raw_message

import websockets

from estock.kafka.producer import create_kafka_producer
from estock.kafka.topics import KIS_STOCK_TRADE_RAW


KST = timezone(timedelta(hours=9))


def get_stock_codes() -> list[str]:
    """
    .env의 KIS_WS_STOCK_CODES 값을 리스트로 변환.

    예:
    KIS_WS_STOCK_CODES=005930,000660
    """
    raw_value = os.getenv("KIS_WS_STOCK_CODES", "005930")

    return [
        code.strip()
        for code in raw_value.split(",")
        if code.strip()
    ]


def build_subscribe_message(
    approval_key: str,
    stock_code: str,
) -> dict:
    """
    KIS 국내주식 실시간 체결가 구독 메시지 생성.

    주의:
    - tr_id, body 구조는 KIS WebSocket 문서 기준으로 최종 확인 필요.
    - 현재는 국내주식 실시간 체결가용 기본 형태로 둔다.
    """
    return {
        "header": {
            "approval_key": approval_key,
            "custtype": "P",
            "tr_type": "1",
            "content-type": "utf-8",
        },
        "body": {
            "input": {
                "tr_id": "H0STCNT0",
                "tr_key": stock_code,
            }
        },
    }


def build_kafka_event(raw_message) -> dict:
    """
    KIS WebSocket 원문 메시지를 Kafka에 넣기 위한 공통 이벤트 형태로 감싼다.
    """
    return {
        "source": "KIS",
        "market": "KRX",
        "tr_id": "H0STCNT0",
        "received_at": datetime.now(KST).isoformat(),
        "raw_message": raw_message,
    }


async def run():
    ws_url = os.getenv("KIS_WS_URL")
    approval_key = os.getenv("KIS_WS_APPROVAL_KEY")
    topic = os.getenv("KAFKA_SOURCE_TOPIC", KIS_STOCK_TRADE_RAW)

    if not ws_url:
        raise ValueError("KIS_WS_URL 환경변수가 없습니다.")

    if not approval_key:
        client = KisClient()
        approval_key = client.get_websocket_approval_key()

    if not approval_key:
        raise ValueError("KIS_WS_APPROVAL_KEY 환경변수가 없습니다.")

    stock_codes = get_stock_codes()

    producer = create_kafka_producer()

    print("[KIS WS Producer Start]")
    print(f"ws_url      : {ws_url}")
    print(f"topic       : {topic}")
    print(f"stock_codes : {stock_codes}")

    async with websockets.connect(
        ws_url,
        ping_interval=None,
    ) as websocket:

        for stock_code in stock_codes:
            subscribe_message = build_subscribe_message(
                approval_key=approval_key,
                stock_code=stock_code,
            )

            await websocket.send(
                json.dumps(subscribe_message, ensure_ascii=False)
            )

            print(f"[SUBSCRIBED] stock_code={stock_code}")

        while True:
            raw_message = await websocket.recv()

            message_type = classify_kis_raw_message(raw_message)

            if message_type == "pingpong":
                await websocket.pong(str(raw_message).encode("utf-8"))

                print("[PINGPONG] received and pong sent")

                continue

            event = build_kafka_event(raw_message)
            event["message_type"] = message_type

            producer.send(
                topic,
                key=None,
                value=event,
            )

            producer.flush()

            print(
                f"[PRODUCED] topic={topic}, "
                f"message_type={message_type}, "
                f"message_length={len(str(raw_message))}"
            )


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()