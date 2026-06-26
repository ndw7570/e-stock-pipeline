"""
Debezium 메시지 → 내부 EmployeeChange dataclass 변환.

[Debezium 메시지 구조 (pgoutput plugin, schemas.enable=false)]
{
  "before": {employee_id: 1, name: "...", ...} | null,
  "after":  {employee_id: 1, name: "...", ...} | null,
  "source": {
    "version": "...", "connector": "postgresql",
    "ts_ms": ..., "snapshot": "false", "db": "interx_op001",
    "schema": "interx_hr", "table": "employee", "lsn": ...
  },
  "op": "c" | "u" | "d" | "r",  # create/update/delete/read(snapshot)
  "ts_ms": 1719337200000
}

[op별 before/after 패턴]
- "c" (create) : before=null, after={새 row}
- "r" (read)   : before=null, after={row}        ← snapshot
- "u" (update) : before={옛 row}, after={새 row}
- "d" (delete) : before={옛 row}, after=null

[null 메시지 = tombstone]
DELETE 후 추가로 보내는 null payload. tombstones.on.delete=false라 안 옴.
혹시 받으면 그냥 skip.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Debezium op 코드
OP_CREATE = "c"
OP_UPDATE = "u"
OP_DELETE = "d"
OP_READ = "r"     # snapshot


@dataclass
class EmployeeChange:
    """Debezium 메시지를 내부 도메인 객체로 변환한 결과."""
    op: str
    employee_id: int | None
    employee_code: str | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    ts_ms: int
    source: dict[str, Any]

    @property
    def is_snapshot(self) -> bool:
        """snapshot 단계에서 온 메시지인지."""
        return self.op == OP_READ

    @property
    def is_delete(self) -> bool:
        return self.op == OP_DELETE


def parse_debezium_event(value: dict | None) -> EmployeeChange | None:
    """
    Debezium JSON value → EmployeeChange.

    Returns:
        EmployeeChange 또는 None (tombstone/잘못된 형식).
    """
    # tombstone
    if value is None:
        return None

    # schemas.enable=true 형식이면 payload 꺼내기
    if isinstance(value, dict) and "payload" in value and "schema" in value:
        value = value["payload"]

    op = value.get("op")
    if op not in (OP_CREATE, OP_UPDATE, OP_DELETE, OP_READ):
        return None

    before = value.get("before")
    after = value.get("after")

    # employee_id/employee_code 추출
    # DELETE는 after=null이라 before에서 가져옴
    payload = after if after is not None else before
    employee_id = payload.get("employee_id") if payload else None
    employee_code = payload.get("employee_code") if payload else None

    return EmployeeChange(
        op=op,
        employee_id=employee_id,
        employee_code=employee_code,
        before=before,
        after=after,
        ts_ms=value.get("ts_ms", 0),
        source=value.get("source", {}),
    )



# @property = 보통 __init__은 생성자가 생성하는 시점 값을 고정함. 그러나, is_delete를 호출할 때 마다 입력 값을 덮어씌워서 최신값을 보장함.
# 더욱이 함수를 함부로 변경할 수 없는 readOnly라네