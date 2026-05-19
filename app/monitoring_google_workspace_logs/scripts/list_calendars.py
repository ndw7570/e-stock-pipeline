from app.monitoring_google_workspace_logs.clients.google_calendar_client import (
    GoogleCalendarClient,
)


def main() -> None:
    client = GoogleCalendarClient()
    cals = client.list_calendars()

    print(f"총 {len(cals)}개 캘린더")
    for c in cals:
        cid = c["id"]
        summary = c.get("summary")
        primary = c.get("primary", False)
        role = c.get("accessRole")
        print(f"  - id={cid}, summary={summary}, primary={primary}, role={role}")


if __name__ == "__main__":
    main()


#검증하기 위한 실행 스크립트