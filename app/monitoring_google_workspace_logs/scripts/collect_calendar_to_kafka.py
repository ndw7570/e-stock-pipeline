from app.monitoring_google_workspace_logs.services.calendar_collector import (
    collect_calendar_events_to_kafka,
)

def main() -> None:
    count = collect_calendar_events_to_kafka()
    print(f"Kafka 발행 완료 {count} 건")


if __name__ == "__main__":
    main()