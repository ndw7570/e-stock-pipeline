from app.monitoring_google_workspace_logs.services.collectors.orchestrate_sync import (
    sync_all_calendars,
)


def main() -> None:
    result = sync_all_calendars()
    print(f"Total changes: {result['total']}")
    print(f"Kafka published: {result['kafka']}")
    print(f"Sync tokens committed: {result['committed_tokens']}")


if __name__ == "__main__":
    main()
