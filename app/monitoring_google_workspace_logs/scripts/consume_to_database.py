from app.monitoring_google_workspace_logs.services.collectors.orchestrate_consume import (
    consume_to_database,
)


def main() -> None:
    result = consume_to_database()
    print(f"Consumed: {result['consumed']}, Skipped: {result['skipped']}")


if __name__ == "__main__":
    main()
