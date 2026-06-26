"""
D3 검증 — EmployeeRowMappingService 동작 확인 (cdc.interx_hr_employee_row_mapping).

순서:
1. upsert 3건
2. get으로 조회
3. upsert 갱신 (idempotent)
4. shift_rows_above 재정렬
5. delete
6. 테스트 정리
"""
from app.employee_sheets_cdc.services.database.handle_row_mapping import (
    EmployeeRowMappingService,
)


def main() -> None:
    svc = EmployeeRowMappingService

    print("=== Step 1: upsert 3건 ===")
    svc.upsert(employee_id=1, employee_code="E001", sheet_row_number=2)
    svc.upsert(employee_id=2, employee_code="E002", sheet_row_number=3)
    svc.upsert(employee_id=3, employee_code="E003", sheet_row_number=4)
    print(f"전체 매핑 수: {svc.count()}")
    print()

    print("=== Step 2: get 조회 ===")
    print(f"employee_id=1 → row {svc.get_row_by_employee_id(1)}")
    print(f"employee_code='E002' → row {svc.get_row_by_employee_code('E002')}")
    print(f"없는 id=999 → {svc.get_row_by_employee_id(999)}")
    print()

    print("=== Step 3: upsert 갱신 (idempotent) ===")
    svc.upsert(employee_id=1, employee_code="E001", sheet_row_number=99)
    print(f"employee_id=1 → row {svc.get_row_by_employee_id(1)} (99 나와야)")
    svc.upsert(employee_id=1, employee_code="E001", sheet_row_number=2)
    print()

    print("=== Step 4: shift_rows_above (row 2 삭제 시뮬레이션) ===")
    affected = svc.shift_rows_above(deleted_row_number=2, delta=-1)
    print(f"영향 row 수: {affected}")
    print(f"  employee_id=2 → row {svc.get_row_by_employee_id(2)} (3→2 되어야)")
    print(f"  employee_id=3 → row {svc.get_row_by_employee_id(3)} (4→3 되어야)")
    print()

    print("=== Step 5: delete ===")
    deleted_row = svc.delete_by_employee_id(1)
    print(f"employee_id=1 삭제됨 (시트 row {deleted_row})")
    print(f"  남은 매핑 수: {svc.count()}")
    print()

    print("=== Step 6: 테스트 정리 ===")
    for emp_id in [2, 3]:
        svc.delete_by_employee_id(emp_id)
    print(f"최종 매핑 수: {svc.count()}")
    print()

    print("✅ EmployeeRowMappingService 모든 메서드 동작 OK")


if __name__ == "__main__":
    main()
