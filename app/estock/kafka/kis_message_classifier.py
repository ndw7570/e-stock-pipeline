import json
from typing import Any


def classify_kis_raw_message(raw_message: Any) -> str:
    """
    KIS WebSocket raw_message 종류 분류.

    반환값:
    - control_json       : SUBSCRIBE SUCCESS 같은 JSON 제어 메시지
    - trade              : H0STCNT0 실시간 체결 데이터
    - pingpong           : PINGPONG / heartbeat 메시지
    - empty              : 빈 메시지
    - unknown            : 아직 알 수 없는 메시지
    """

    if raw_message is None:
        return "empty"

    raw_text = str(raw_message).strip()

    if not raw_text:
        return "empty"

    if "PINGPONG" in raw_text.upper():
        return "pingpong"

    if raw_text.startswith("{"):
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            return "unknown"

        header = data.get("header", {})
        body = data.get("body", {})

        msg1 = body.get("msg1")
        rt_cd = body.get("rt_cd")
        tr_id = header.get("tr_id")

        if msg1 or rt_cd is not None or tr_id:
            return "control_json"

        return "unknown"

    if raw_text.startswith("0|H0STCNT0"):
        return "trade"

    if "H0STCNT0" in raw_text and "^" in raw_text:
        return "trade"

    return "unknown"