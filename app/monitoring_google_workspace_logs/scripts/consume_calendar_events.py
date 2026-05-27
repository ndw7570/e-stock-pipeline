from app.monitoring_google_workspace_logs.services.collectors.sources.calendar_kafka import (
    consume_calendar_changes,
)


def main() -> None:
    count = 0
    counts_by_type: dict[str, int] = {}

    for msg in consume_calendar_changes():
        change_type = msg.get("change_type", "?")
        event = msg.get("event", {})
        event_id = event.get("id", "?")
        summary = event.get("summary", "(no title)")

        print(f"[{change_type:9s}] {event_id[:30]:30s} | {summary}")

        count += 1
        counts_by_type[change_type] = counts_by_type.get(change_type, 0) + 1

    print(f"\n=== {count} messages consumed ===")
    for k, v in sorted(counts_by_type.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()