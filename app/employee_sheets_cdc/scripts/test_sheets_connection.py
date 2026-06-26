"""
D2 검증 — GoogleSheetsClient 동작 확인.

테스트 순서:
1. 시트 연결 (메타데이터 조회)
2. 헤더 자동 초기화 (interx_hr.employee 컬럼)
3. 더미 데이터 1행 append
4. 그 row 읽기
5. 그 row 업데이트
6. 그 row 삭제 (마지막)
"""
import os

from app.employee_sheets_cdc.clients.google_sheets_client import GoogleSheetsClient


SPREADSHEET_ID = os.getenv(
    "EMPLOYEE_SHEET_ID",
    "1Fl18t5hrmfqkYey84ZeIOfxzqvDBYw6P9yUbyF7vxXU",
)
SHEET_NAME = os.getenv("EMPLOYEE_SHEET_TAB", "ems_api")

# interx_hr.employee 컬럼 (42개) — DB 컬럼 순서 그대로
EMPLOYEE_COLUMNS = [
    "employee_id", "employment_status", "employment_type", "employee_name",
    "employee_code", "gender", "birth_date", "phone_number", "hire_date",
    "resignation_date", "last_working_date", "hire_cancellation_date",
    "leave_start_date", "leave_end_date", "disciplinary_start_date",
    "disciplinary_end_date", "primary_work_location",
    "primary_job_responsibilities", "company_email", "personal_email",
    "onboarding_documents_url", "onboarding_leader_name",
    "resident_registration_no", "nationality_code", "visa_info",
    "passport_english_name", "highest_school_name", "major",
    "highest_degree", "degree_certificate_no", "highest_degree_url",
    "military_service_info", "remarks", "is_deleted", "dept3_id",
    "position_id", "research_center_id",
    "research_center_appointment_date", "research_role_type",
    "calculated_employment_status", "employment_status_calculated_at",
    "display_title",
]


def main() -> None:
    client = GoogleSheetsClient(
        spreadsheet_id=SPREADSHEET_ID,
        sheet_name=SHEET_NAME,
    )

    # 1) 헤더 초기화
    print("=== Step 1: 헤더 초기화 ===")
    created = client.ensure_header(EMPLOYEE_COLUMNS)
    print(f"헤더 새로 작성: {created} (False면 이미 있던 헤더 유지)")
    header = client.get_header()
    print(f"현재 헤더 컬럼 수: {len(header)}")
    print()

    # 2) 더미 데이터 append
    print("=== Step 2: 더미 행 append ===")
    dummy_values = [str(i) for i in range(len(EMPLOYEE_COLUMNS))]
    dummy_values[3] = "테스트직원"
    dummy_values[4] = "TEST_001"
    new_row = client.append_row(dummy_values)
    print(f"추가된 row 번호: {new_row}")
    print()

    # 3) 전체 행 수 확인
    print("=== Step 3: 시트 전체 읽기 ===")
    all_rows = client.get_all_values()
    print(f"전체 행 수 (헤더 포함): {len(all_rows)}")
    print()

    # 4) 그 row 업데이트
    print("=== Step 4: 추가한 row 업데이트 ===")
    dummy_values[3] = "업데이트된이름"
    client.update_row(new_row, dummy_values)
    print(f"row {new_row} 업데이트 완료")
    print()

    # 5) 그 row 삭제 (테스트 정리)
    print("=== Step 5: 테스트 행 삭제 ===")
    client.delete_row(new_row)
    print(f"row {new_row} 삭제 완료")
    print()

    print("✅ GoogleSheetsClient 모든 메서드 동작 OK")


if __name__ == "__main__":
    main()
