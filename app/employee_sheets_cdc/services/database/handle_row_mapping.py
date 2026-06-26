"""
Employee Row Mapping CRUD Service.

[메서드]
- upsert                       : 새 매핑 추가 또는 갱신 (idempotent)
- get_row_by_employee_id       : 핵심 조회 (Consumer 변경 처리 시)
- get_row_by_employee_code     : 사람용 코드로 조회
- delete_by_employee_id        : 매핑 삭제 (직원 퇴사 등)
- shift_rows_above             : Row 삭제 후 그 아래 row 번호 재정렬 ⭐
- get_all                      : 전체 매핑 (디버깅용)
- count                        : 총 매핑 수

[shift_rows_above]
시트 row 5 삭제 → row 6~∞ 한 칸 위로 → 매핑도 sheet_row_number -1 해야 동기화.
"""
from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.common.db_core import session_scope
from app.employee_sheets_cdc.services.database.model.row_mapping import (
    EmployeeRowMapping,
    EmployeeRowMappingModel,
)


class EmployeeRowMappingService:

    @staticmethod
    def upsert(employee_id: int, employee_code: str, sheet_row_number: int) -> None:
        """
        매핑 새로 추가 또는 갱신. 같은 employee_id면 덮어쓰기 (idempotent).
        Postgres INSERT ... ON CONFLICT DO UPDATE 사용.
        """
        with session_scope() as s:
            stmt = pg_insert(EmployeeRowMapping).values(
                employee_id=employee_id,
                employee_code=employee_code,
                sheet_row_number=sheet_row_number,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["employee_id"],
                set_={
                    "employee_code": stmt.excluded.employee_code,
                    "sheet_row_number": stmt.excluded.sheet_row_number,
                },
            )
            s.execute(stmt)

    @staticmethod
    def get_row_by_employee_id(employee_id: int) -> int | None:
        """employee_id로 sheet_row_number 조회. 없으면 None."""
        with session_scope() as s:
            return s.execute(
                select(EmployeeRowMapping.sheet_row_number).where(
                    EmployeeRowMapping.employee_id == employee_id,
                )
            ).scalar_one_or_none()

    @staticmethod
    def get_row_by_employee_code(employee_code: str) -> int | None:
        """employee_code로 sheet_row_number 조회."""
        with session_scope() as s:
            return s.execute(
                select(EmployeeRowMapping.sheet_row_number).where(
                    EmployeeRowMapping.employee_code == employee_code,
                )
            ).scalar_one_or_none()

    @staticmethod
    def delete_by_employee_id(employee_id: int) -> int | None:
        """
        매핑 삭제. 반환: 삭제된 row의 sheet_row_number (없으면 None).
        호출자가 이 row_number를 알아야 shift_rows_above 호출 가능.
        """
        with session_scope() as s:
            row_number = s.execute(
                select(EmployeeRowMapping.sheet_row_number).where(
                    EmployeeRowMapping.employee_id == employee_id,
                )
            ).scalar_one_or_none()
            if row_number is None:
                return None

            s.execute(
                delete(EmployeeRowMapping).where(
                    EmployeeRowMapping.employee_id == employee_id
                )
            )
            return row_number

    @staticmethod
    def shift_rows_above(deleted_row_number: int, delta: int = -1) -> int:
        """
        시트에서 row 삭제 시 그 아래 row들이 한 칸 위로 → 매핑도 동기화.

        Args:
            deleted_row_number: 시트에서 삭제된 row 번호
            delta: 보통 -1 (한 칸 위로 시프트)

        Returns:
            영향받은 row 수
        """
        with session_scope() as s:
            result = s.execute(
                update(EmployeeRowMapping)
                .where(EmployeeRowMapping.sheet_row_number > deleted_row_number)
                .values(
                    sheet_row_number=EmployeeRowMapping.sheet_row_number + delta
                )
            )
            return result.rowcount

    @staticmethod
    def get_all() -> list[EmployeeRowMappingModel]:
        """전체 매핑 list 반환 (디버깅용)."""
        with session_scope() as s:
            rows = s.execute(select(EmployeeRowMapping)).scalars().all()
            return [r.to_dto() for r in rows]

    @staticmethod
    def count() -> int:
        """전체 매핑 수."""
        with session_scope() as s:
            return s.execute(
                select(func.count()).select_from(EmployeeRowMapping)
            ).scalar_one()
