"""
Employee Row Mapping 모델 + DTO.

[메커니즘]
employee_id (DB PK 불변)  ←→  sheet_row_number (시트 위치)
   + employee_code (사람용 사번, 참조 편의)

Consumer가 변경 이벤트 받으면:
  1. event.employee_id → row_number 조회 (이 테이블)
  2. row_number로 Sheets API 호출

[테이블 위치]
cdc.interx_hr_employee_row_mapping
- 스키마 'cdc' = 모든 CDC 관련 보관 (확장 시 cdc.* 추가)
- 테이블 명명 규칙: <source_schema>_<source_table>_<purpose>
  - interx_hr  : source DB의 스키마
  - employee   : source DB의 테이블
  - row_mapping: 이 테이블의 목적 (시트 row 매핑)

미래 확장 예시:
  cdc.interx_hr_department_row_mapping  ← 같은 source 다른 테이블
  cdc.hr_v2_employee_row_mapping        ← 다른 source DB
  cdc.interx_hr_employee_sync_state     ← 다른 purpose

[왜 employee_id를 PK로?]
- DB 시퀀셜 키 → 절대 변경 X
- Kafka 메시지 키와 일치 → 조회 단순
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, func

from app.common.db_core import Base


@dataclass
class EmployeeRowMappingModel:
    """Employee Row Mapping DTO (서비스/API 간 데이터 전달용)."""
    employee_id: int
    employee_code: str
    sheet_row_number: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EmployeeRowMapping(Base):
    """
    SQLAlchemy 모델 — cdc.interx_hr_employee_row_mapping 테이블.
    """
    __tablename__ = "interx_hr_employee_row_mapping"
    __table_args__ = {"schema": "cdc"}

    employee_id = Column(BigInteger, primary_key=True, autoincrement=False)
    employee_code = Column(String(20), unique=True, nullable=False, index=True)
    sheet_row_number = Column(Integer, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dto(self) -> EmployeeRowMappingModel:
        return EmployeeRowMappingModel(
            employee_id=self.employee_id,
            employee_code=self.employee_code,
            sheet_row_number=self.sheet_row_number,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
