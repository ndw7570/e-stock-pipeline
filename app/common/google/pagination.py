from __future__ import annotations

from typing import Any, Callable

# page_token을 받아 googleapiclient request 객체를 만드는 함수.
# request 객체는 .execute()를 통해 실제 HTTP 호출이 일어난다.
RequestFactory = Callable[[str | None], Any]


def paginate_google_api(
    request_factory: RequestFactory,
    items_key: str = "items",
) -> list[dict[str, Any]]:
    """
    Google API 페이지네이션 공통 헬퍼.

    nextPageToken을 따라가며 모든 페이지의 항목을 누적해서 반환한다.

    Args:
        request_factory:
            page_token을 받아 googleapiclient request 객체를 만드는 함수.
            예:
                lambda token: service.events().list(
                    calendarId=cal_id,
                    pageToken=token,
                    ...
                )
        items_key:
            응답 dict에서 데이터 항목이 들어있는 키.
            - Calendar / 대부분 Google API → "items"
            - Drive → "files"
            - Admin Reports → "activities"

    Returns:
        모든 페이지의 항목을 합친 list.
    """
    items: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        response = request_factory(page_token).execute()
        items.extend(response.get(items_key, []))

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return items


def paginate_google_api_with_sync_token(
    request_factory: RequestFactory,
    items_key: str = "items",
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Google API 페이지네이션 + nextSyncToken 회수.

    Calendar처럼 증분 동기화를 지원하는 API에서 사용한다.
    nextSyncToken은 보통 마지막 페이지에만 포함되므로
    모든 페이지를 끝까지 받아야 얻을 수 있다.

    Args:
        request_factory:
            page_token을 받아 request 객체를 만드는 함수.
        items_key:
            응답 dict의 항목 키 (기본 "items").

    Returns:
        (모든 페이지의 항목 list, next_sync_token 또는 None)
    """
    items: list[dict[str, Any]] = []
    page_token: str | None = None
    next_sync_token: str | None = None

    while True:
        response = request_factory(page_token).execute()
        items.extend(response.get(items_key, []))

        page_token = response.get("nextPageToken")
        next_sync_token = response.get("nextSyncToken")

        if not page_token:
            break

    return items, next_sync_token
