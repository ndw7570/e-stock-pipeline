from datetime import datetime, timedelta, timezone
from typing import Any


KST = timezone(timedelta(hours=9))


def parse_kis_trade_raw_message(raw_message: Any) -> dict:
    """
    KIS H0STCNT0 실시간 체결 raw_message 1차 파서.

    현재 단계에서는 실제 장중 체결 raw 샘플을 아직 못 봤기 때문에
    필드명을 확정하지 않고 raw_fields로 안전하게 보존한다.

    예상 형태:
    0|H0STCNT0|...|005930^...^...
    """
    raw_text = str(raw_message).strip()

    parts = raw_text.split("|")

    if len(parts) < 4:
        raise ValueError(f"KIS trade raw_message 형식이 예상과 다릅니다: {raw_text}")

    prefix = parts[0]
    tr_id = parts[1]
    data_count = parts[2]
    payload = parts[3]

    fields = payload.split("^")

    stock_code = fields[0] if len(fields) > 0 else None

    return {
        "source": "KIS",
        "market": "KRX",
        "tr_id": tr_id,
        "prefix": prefix,
        "data_count": data_count,
        "stock_code": stock_code,
        "parsed_at": datetime.now(KST).isoformat(),
        "raw_fields": fields,
        "raw_message": raw_text,
    }