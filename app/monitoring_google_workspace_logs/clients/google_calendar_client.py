from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.common.config.settings import settings
from app.common.google.auth_client import GoogleAuthClient
from app.common.google.pagination import (
    paginate_google_api,
    paginate_google_api_with_sync_token,
)


CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
CALENDAR_LIST_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.calendarlist.readonly"


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
        # 캘린더 전용 토큰 사용 → drive 토큰과 격리 (서로 덮어쓰지 않음)
        self.auth_client = auth_client or GoogleAuthClient(
            token_path=settings.google_workspace.token_calendar_path,
        )

        self.service = self.auth_client.build_service(
            service_name="calendar",
            version="v3",
            scopes=[CALENDAR_READONLY_SCOPE, CALENDAR_LIST_READONLY_SCOPE],
        )

    def list_events_by_time_range(
        self,
        calendar_id: str | None = None,        # ← 새 인자, 첫 번째 위치
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
        cal_id = calendar_id or self.calendar_id
        now = datetime.now(timezone.utc)

        if time_min is None:
            time_min = now - timedelta(days=30)

        if time_max is None:
            time_max = now + timedelta(days=30)

        return paginate_google_api(
            lambda token: self.service.events().list(
                calendarId=cal_id,
                timeMin=self._to_rfc3339(time_min),
                timeMax=self._to_rfc3339(time_max),
                singleEvents=True,
                orderBy="startTime",
                maxResults=max_results,
                pageToken=token,
            )
        )

    def list_calendars(self) -> list[dict[str, Any]]:
        """
        이 OAuth 토큰으로 접근 가능한 모든 캘린더 목록을 반환한다.

        Returns:
            Google CalendarList 항목 dict 목록.
            각 항목에는 id, summary, primary(bool), accessRole 등이 들어있다.

            주요 필드:
            - id: 캘린더 ID (events.list 호출 시 calendarId 인자로 사용)
            - summary: 캘린더 이름
            - primary: 본인 주 캘린더 여부
            - accessRole: owner / reader / writer / freeBusyReader
        """
        return paginate_google_api(
            lambda token: self.service.calendarList().list(
                maxResults=250,
                pageToken=token,
            )
        )

    def list_events_by_sync_token(
        self,
        sync_token: str,
        calendar_id: str | None = None,
        max_results: int = 250,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """
        sync_token 기반으로 변경된 Calendar 이벤트만 조회한다.

        Args:
            sync_token:
                이전 전체 수집 또는 증분 수집 결과에서 받은 nextSyncToken.
            calendar_id:
                조회할 캘린더 ID. None이면 인스턴스 기본값(self.calendar_id) 사용.
            max_results:
                API 요청당 최대 이벤트 수.

        Returns:
            (이벤트 목록, 다음 sync_token)

        주의:
            sync_token이 만료되면 Google API가 410 Gone 에러를 반환할 수 있다.
            그 경우 전체 재수집을 수행해야 한다.
        """
        cal_id = calendar_id or self.calendar_id

        return paginate_google_api_with_sync_token(
            lambda token: self.service.events().list(
                calendarId=cal_id,
                syncToken=sync_token,
                singleEvents=True,
                maxResults=max_results,
                pageToken=token,
            )
        )

    def list_events_for_initial_sync(
        self,
        calendar_id: str | None = None,
        max_results: int = 250,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """
        최초 수집용 Calendar 이벤트 조회.

        캘린더의 전체 이벤트를 받고 nextSyncToken을 회수한다.
        이 token을 저장하면 다음부터 증분 수집(list_events_by_sync_token)이 가능하다.

        주의:
            Google API 정책상 nextSyncToken을 받으려면 timeMin/timeMax/orderBy/q
            같은 필터를 사용할 수 없다. 그래서 이 메서드는 캘린더의 전체 이벤트를 받는다.
            기간 필터가 필요하면 list_events_by_time_range()를 쓰되, 그 경우 sync_token은
            받을 수 없다.

        Args:
            calendar_id:
                조회할 캘린더 ID. None이면 인스턴스 기본값(self.calendar_id) 사용.

        Returns:
            (이벤트 목록, next_sync_token)
        """
        cal_id = calendar_id or self.calendar_id

        return paginate_google_api_with_sync_token(
            lambda token: self.service.events().list(
                calendarId=cal_id,
                singleEvents=True,
                maxResults=max_results,
                pageToken=token,
            )
        )


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