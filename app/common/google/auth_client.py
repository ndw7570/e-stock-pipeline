from __future__ import annotations

from pathlib import Path
from typing import Sequence

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from app.common.config.settings import settings


class GoogleAuthClient:
    """
    Google Workspace API 인증 공통 클라이언트.

    역할:
    - credentials.json 기반 OAuth 인증
    - token.json 저장 및 재사용
    - access token 만료 시 refresh
    - Calendar / Drive / Reports API service 객체 생성

    이 파일은 Google API 인증만 담당한다.
    Calendar 이벤트 조회, Drive 파일 조회 같은 도메인 로직은
    별도 client 파일에서 처리한다.
    """

    def __init__(
        self,
        credentials_path: str | None = None,
        token_path: str | None = None,
    ) -> None:
        self.credentials_path = Path(
            credentials_path or settings.google_workspace.credentials_path
        )
        self.token_path = Path(
            token_path or settings.google_workspace.token_path
        )

    # Sequence[str]로 적으면 → "순서 있는 문자열 컬렉션이면 뭐든 OK" (list든 tuple든).
    def get_credentials(self, scopes: Sequence[str]) -> Credentials:
        """
        주어진 scope에 맞는 Google Credentials 객체를 반환한다.

        Args:
            scopes:
                Google API 권한 범위 목록.
                예:
                - Calendar read only
                - Drive read only
                - Drive activity read only

        Returns:
            인증 완료된 Credentials 객체
        """
        credentials: Credentials | None = None

        if self.token_path.exists():
            credentials = Credentials.from_authorized_user_file(
                filename=str(self.token_path),
                scopes=list(scopes),
            )

        if credentials and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self._save_token(credentials)
            return credentials

        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Google credentials file not found: {self.credentials_path}"
            )

        # 로컬에 임시 웹서버 띄우고, 브라우저를 Google 동의 페이지로 자동 오픈 (flow + run_local_server)
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_file=str(self.credentials_path),
            scopes=list(scopes),
        )

        credentials = flow.run_local_server(
            port=0,                 #OS가 비어있는 포트 자동 할당 → 충돌 없음
            prompt="consent",       # 매번 동의 화면 강제 표시 + refresh_token 반드시 발급,  생략하면 → 이미 동의한 적 있는 사용자는 화면 건너뜀 + refresh_token이 안 나올 수 있음
        )

        self._save_token(credentials)

        return credentials

    def build_service(
        self,
        service_name: str,
        version: str,
        scopes: Sequence[str],
    ) -> Resource:
        """
        Google API service 객체를 생성한다.

        Args:
            service_name:
                Google API 이름.
                예: "calendar", "drive", "admin"

            version:
                API version.
                예: "v3", "reports_v1"

            scopes:
                필요한 OAuth scope 목록.

        Returns:
            googleapiclient Resource 객체
        """
        credentials = self.get_credentials(scopes=scopes)

        # Google API 클라이언트 라이브러리가 제공하는 build() 함수를 사용해서, URL 조합, 캐시 Hit
        return build(
            serviceName=service_name,
            version=version,
            credentials=credentials,
        )

    def _save_token(self, credentials: Credentials) -> None:
        """
        인증 토큰을 token.json으로 저장한다.
        """
        self.token_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.token_path.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )