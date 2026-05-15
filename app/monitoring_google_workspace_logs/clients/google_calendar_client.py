from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.common.config.settings import settings
from app.monitoring_google_workspace_logs.clients.google_auth_client import (
    GoogleAuthClient,
)


CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


class GoogleCalendarClient:
    """
    Google Calendar API 조회 클라이언트.

    역할:
    - GoogleAuthClient를 사용해 Calendar API service 생성
    - 특정 기간의 Calendar 이벤트 조회
    - 증분 수집용 sync_token 기반 이벤트 조회
    - Google API 응답을 Python dict로 반환

    이 클래스는 Kafka나 DB를 모른다.
    오직 Calendar API 호출만 담당한다.
    """

    def __init__(
        self,
        calendar_id: str | None = None,
        auth_client: GoogleAuthClient | None = None,
    ) -> None:
        self.calendar_id = calendar_id or settings.google_workspace.calendar_id
        self.auth_client = auth_client or GoogleAuthClient()

        self.service = self.auth_client.build_service(
            service_name="calendar",
            version="v3",
            scopes=[CALENDAR_READONLY_SCOPE],
        )

    def list_events_by_time_range(
        self,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 250,
    ) -> list[dict[str, Any]]:
        """
        특정 기간의 Calendar 이벤트 목록을 조회한다.

        Args:
            time_min:
                조회 시작 시각. None이면 현재 시각 기준 30일 전.
            time_max:
                조회 종료 시각. None이면 현재 시각 기준 30일 후.
            max_results:
                API 요청당 최대 이벤트 수.

        Returns:
            Google Calendar 이벤트 dict 목록.
        """
        now = datetime.now(timezone.utc)

        if time_min is None:
            time_min = now - timedelta(days=30)

        if time_max is None:
            time_max = now + timedelta(days=30)

        events: list[dict[str, Any]] = []
        page_token: str | None = None

        while True:
            response = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=self._to_rfc3339(time_min),
                    timeMax=self._to_rfc3339(time_max),
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=max_results,
                    pageToken=page_token,
                )
                .execute()
            )

            events.extend(response.get("items", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return events

    def list_events_by_sync_token(
        self,
        sync_token: str,
        max_results: int = 250,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """
        sync_token 기반으로 변경된 Calendar 이벤트만 조회한다.

        Args:
            sync_token:
                이전 전체 수집 또는 증분 수집 결과에서 받은 nextSyncToken.
            max_results:
                API 요청당 최대 이벤트 수.

        Returns:
            (이벤트 목록, 다음 sync_token)

        주의:
            sync_token이 만료되면 Google API가 410 Gone 에러를 반환할 수 있다.
            그 경우 전체 재수집을 수행해야 한다.
        """
        events: list[dict[str, Any]] = []
        page_token: str | None = None
        next_sync_token: str | None = None

        while True:
            response = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    syncToken=sync_token,
                    singleEvents=True,
                    maxResults=max_results,
                    pageToken=page_token,
                )
                .execute()
            )

            events.extend(response.get("items", []))

            page_token = response.get("nextPageToken")
            next_sync_token = response.get("nextSyncToken")

            if not page_token:
                break

        return events, next_sync_token

    def list_events_for_initial_sync(
        self,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 250,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """
        최초 수집용 Calendar 이벤트 조회.

        일반 기간 조회와 비슷하지만, 마지막에 nextSyncToken을 받는 것이 목적이다.
        이 token을 저장해두면 다음부터 증분 수집이 가능하다.

        Returns:
            (이벤트 목록, next_sync_token)
        """
        now = datetime.now(timezone.utc)

        if time_min is None:
            time_min = now - timedelta(days=30)

        if time_max is None:
            time_max = now + timedelta(days=30)

        events: list[dict[str, Any]] = []
        page_token: str | None = None
        next_sync_token: str | None = None

        while True:
            response = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=self._to_rfc3339(time_min),
                    timeMax=self._to_rfc3339(time_max),
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=max_results,
                    pageToken=page_token,
                )
                .execute()
            )

            events.extend(response.get("items", []))

            page_token = response.get("nextPageToken")
            next_sync_token = response.get("nextSyncToken")

            if not page_token:
                break

        return events, next_sync_token

    @staticmethod
    def _to_rfc3339(value: datetime) -> str:
        """
        Google Calendar API가 요구하는 RFC3339 datetime 문자열로 변환한다.

        예:
            2026-05-15T01:23:45Z
        """
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")