from __future__ import annotations

import io
from typing import Any

from googleapiclient.http import MediaIoBaseDownload

from app.monitoring_google_workspace_logs.clients.google_auth_client import (
    GoogleAuthClient,
)
from app.monitoring_google_workspace_logs.clients.pagination import (
    paginate_google_api,
)


DRIVE_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"


# Google Docs/Sheets/Slides는 자체 포맷이라 그냥 다운로드 불가 → export 필요.
# 각 포맷의 plain text export MIME type 매핑.
GOOGLE_NATIVE_EXPORT_MIME = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
    "application/vnd.google-apps.presentation": "text/plain",
}


class GoogleDriveClient:
    """
    Google Drive API 조회 클라이언트.

    역할:
    - GoogleAuthClient를 사용해 Drive API service 생성
    - 본인 계정의 파일 목록 조회 (files.list)
    - 파일 메타데이터 조회 (files.get)
    - 파일 다운로드 (일반 바이너리 또는 Google Docs export)

    이 클래스는 Kafka, DB, 파싱을 모른다.
    오직 Drive API 호출만 담당한다.
    """

    def __init__(
        self,
        auth_client: GoogleAuthClient | None = None,
    ) -> None:
        self.auth_client = auth_client or GoogleAuthClient()
        self._service = self.auth_client.build_service(
            service_name="drive",
            version="v3",
            scopes=[DRIVE_READONLY_SCOPE],
        )

    def list_files(
        self,
        query: str | None = None,
        page_size: int = 100,
        fields: str = (
            "nextPageToken, files(id, name, mimeType, size, modifiedTime, "
            "owners, webViewLink, parents)"
        ),
    ) -> list[dict[str, Any]]:
        """
        본인 Drive의 파일 목록을 list로 반환.

        Args:
            query: Drive API 검색 쿼리. 예: "mimeType='application/pdf'"
            page_size: 한 페이지 파일 수 (최대 1000)
            fields: 응답에 포함할 필드

        Returns:
            파일 메타데이터 dict 리스트
        """
        def request_factory(page_token: str | None):
            return self._service.files().list(
                q=query,
                pageSize=page_size,
                fields=fields,
                pageToken=page_token,
                corpora="user",  # 본인이 접근 가능한 파일만
            )

        return paginate_google_api(request_factory, items_key="files")

    def get_file_metadata(
        self,
        file_id: str,
        fields: str = "id, name, mimeType, size, modifiedTime, owners, webViewLink",
    ) -> dict[str, Any]:
        """파일 1개의 메타데이터 조회."""
        return self._service.files().get(
            fileId=file_id,
            fields=fields,
        ).execute()

    def download_file(
        self,
        file_id: str,
        mime_type: str,
    ) -> bytes:
        """
        파일의 raw 바이트 다운로드.

        - Google Docs/Sheets/Slides: export API로 plain text/csv 변환
        - 일반 파일 (PDF, images, etc): get_media로 원본 다운로드
        """
        if mime_type in GOOGLE_NATIVE_EXPORT_MIME:
            export_mime = GOOGLE_NATIVE_EXPORT_MIME[mime_type]
            request = self._service.files().export_media(
                fileId=file_id,
                mimeType=export_mime,
            )
        else:
            request = self._service.files().get_media(fileId=file_id)

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        return buffer.getvalue()
