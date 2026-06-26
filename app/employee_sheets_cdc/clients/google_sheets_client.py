"""
Google Sheets API 클라이언트.

[책임]
- Spreadsheet read/append/update/delete
- 헤더 자동 초기화 (시트 1행 비어있으면 컬럼명 작성)

[Sheets API 핵심 개념]
- spreadsheet_id  : 파일 전체 ID (URL의 /d/{ID})
- sheet_name      : 워크시트(탭) 이름 ("ems_api" 등)
- range           : "탭이름!A1:Z" 형식 (A1 표기법)
- values          : 2차원 list (rows of columns)
"""
from __future__ import annotations

from typing import Any

from app.common.config.settings import settings
from app.common.google.auth_client import GoogleAuthClient


SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


class GoogleSheetsClient:
    """
    spreadsheet_id + sheet_name 페어로 동작하는 시트 클라이언트.
    한 인스턴스 = 한 워크시트 담당.
    """

    def __init__(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        auth_client: GoogleAuthClient | None = None,
    ) -> None:
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name

        # Sheets 전용 토큰 사용 → calendar/drive 토큰과 격리
        self.auth_client = auth_client or GoogleAuthClient(
            token_path=settings.google_workspace.token_sheets_path,
        )
        self._service = self.auth_client.build_service(
            service_name="sheets",
            version="v4",
            scopes=[SHEETS_SCOPE],
        )

    # ================== READ ==================

    def get_all_values(self) -> list[list[str]]:
        """시트 전체 값을 2D list로 반환. 첫 row=헤더, 빈 시트면 []"""
        result = self._service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=self.sheet_name,
        ).execute()
        return result.get("values", [])

    def get_header(self) -> list[str]:
        """1행 (헤더) 만 읽기."""
        result = self._service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.sheet_name}!1:1",
        ).execute()
        rows = result.get("values", [])
        return rows[0] if rows else []

    # ================== HEADER 초기화 ==================

    def ensure_header(self, columns: list[str]) -> bool:
        """
        시트 1행이 비어있으면 컬럼명 작성. 이미 있으면 안 건드림.

        Returns:
            True: 헤더 새로 작성
            False: 이미 있음 (덮어쓰지 X)
        """
        current = self.get_header()
        if current:
            return False

        self._service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.sheet_name}!A1",
            valueInputOption="RAW",
            body={"values": [columns]},
        ).execute()
        return True

    # ================== APPEND (INSERT) ==================

    def append_row(self, values: list[Any]) -> int:
        """
        시트 마지막에 새 행 추가. 추가된 row 번호 반환 (1-based).
        """
        result = self._service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=self.sheet_name,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [values]},
        ).execute()

        updated_range = result.get("updates", {}).get("updatedRange", "")
        return self._extract_row_number(updated_range)

    # ================== UPDATE ==================

    def update_row(self, row_number: int, values: list[Any]) -> None:
        """특정 row의 모든 셀을 새 values로 업데이트."""
        self._service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.sheet_name}!A{row_number}",
            valueInputOption="RAW",
            body={"values": [values]},
        ).execute()

    # ================== DELETE ==================

    def delete_row(self, row_number: int) -> None:
        """
        특정 row 완전 삭제 (다음 행들 한 칸씩 올라감).
        헤더(1행)는 삭제 금지.
        """
        if row_number <= 1:
            raise ValueError("헤더 row는 삭제할 수 없습니다.")

        sheet_gid = self._get_sheet_gid()
        self._service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={
                "requests": [{
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_gid,
                            "dimension": "ROWS",
                            "startIndex": row_number - 1,
                            "endIndex": row_number,
                        }
                    }
                }]
            },
        ).execute()

    # ================== 헬퍼 ==================

    def _get_sheet_gid(self) -> int:
        """sheet_name (탭 이름) → sheet_gid (숫자 ID) 변환."""
        meta = self._service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id,
            fields="sheets(properties(sheetId,title))",
        ).execute()
        for sheet in meta.get("sheets", []):
            props = sheet["properties"]
            if props["title"] == self.sheet_name:
                return props["sheetId"]
        raise ValueError(f"Sheet '{self.sheet_name}' not found")

    @staticmethod
    def _extract_row_number(updated_range: str) -> int:
        """'ems_api!A123:AP123' → 123"""
        cell = updated_range.split("!")[-1].split(":")[0]
        digits = "".join(c for c in cell if c.isdigit())
        return int(digits) if digits else 0
