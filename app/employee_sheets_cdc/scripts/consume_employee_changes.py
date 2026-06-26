"""
D5 검증 — Kafka에서 Debezium 메시지 받아 출력.

Phase 1: 출력만. Sheets sink는 D6에서.
"""
from app.employee_sheets_cdc.services.parsers.debezium_event_parser import (
    EmployeeChange,
    parse_debezium_event,
)
from app.employee_sheets_cdc.services.sources.employee_changes_kafka import (
    consume_employee_changes,
)
import time
import sys


# 검증용 group_id — earliest로 처음부터 다시 받기 위해 매번 다른 이름
GROUP_ID = f"employee-sheets-cdc-debug-{int(time.time())}"

def main() -> None:
    # Docker에서 Python print는 buffer에 갇혀 안 보일 수 있다.
    # sys.stdout.reconfigure(line_buffering=True)로 개행마다 즉시 출력 강제.
    sys.stdout.reconfigure(line_buffering=True)
    print(f"=== Kafka Consumer 시작 ===")
    print(f"  topic    : dbz.interx_hr.employee")
    print(f"  group_id : {GROUP_ID}")
    print(f"  Ctrl+C로 중단")
    print()

    counts = {"c": 0, "u": 0, "d": 0, "r": 0, "skip": 0}

    for msg in consume_employee_changes(
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
    ):
        event = parse_debezium_event(msg["value"])

        if event is None:
            counts["skip"] += 1
            print(f"[SKIP] tombstone or invalid (offset={msg['offset']})")
            continue

        counts[event.op] = counts.get(event.op, 0) + 1
        _print_event(event, msg["offset"])

        # 통계 (10개마다)
        total = sum(counts.values())
        if total % 10 == 0:
            print(f"  📊 누적: {counts}")
            print()


def _print_event(event: EmployeeChange, offset: int) -> None:
    """이벤트 1건을 한 줄 + 상세로 출력."""
    op_label = {
        "c": "CREATE  ",
        "u": "UPDATE  ",
        "d": "DELETE  ",
        "r": "SNAPSHOT",
    }.get(event.op, event.op.upper())

    print(
        f"[{op_label}] offset={offset:>5} | "
        f"employee_id={event.employee_id} | "
        f"employee_code={event.employee_code}"
    )

    if event.op == "u" and event.before and event.after:
        # 변경된 컬럼만 표시
        changed = [
            (k, event.before.get(k), event.after.get(k))
            for k in event.after.keys()
            if event.before.get(k) != event.after.get(k)
        ]
        if changed:
            print(f"    변경: {len(changed)}개 컬럼")
            for k, old, new in changed[:3]:  # 처음 3개만
                print(f"      {k}: {old!r} → {new!r}")


if __name__ == "__main__":
    main()
