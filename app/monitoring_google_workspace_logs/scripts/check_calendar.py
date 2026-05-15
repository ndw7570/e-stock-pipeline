from app.monitoring_google_workspace_logs.clients.google_calendar_client import (
    GoogleCalendarClient,
)


def main() -> None:
    client = GoogleCalendarClient()

    events = client.list_events_by_time_range()

    print(f"event count: {len(events)}")

    for event in events[:5]:
        print("-" * 80)
        print(f"id: {event.get('id')}")
        print(f"summary: {event.get('summary')}")
        print(f"status: {event.get('status')}")
        print(f"start: {event.get('start')}")
        print(f"end: {event.get('end')}")


if __name__ == "__main__":
    main()
