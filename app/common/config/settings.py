import os
from dataclasses import dataclass
from pathlib import Path

# settings.py 위치: <ROOT>/app/common/config/settings.py
# parents[0]=config, [1]=common, [2]=app, [3]=프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[3]


# 상황	반환되는 값
# POSTGRES_HOST가 OS에 설정돼 있음 (예: db.prod.internal)	"db.prod.internal"
# POSTGRES_HOST가 설정 안 됨	"localhost" (default)
def get_env(name: str, default: str | None = None, required: bool = False) -> str:
    """
    환경변수를 안전하게 읽는 공통 함수.

    - required=True 인데 값이 없으면 명확하게 에러 발생
    - default가 있으면 환경변수가 없을 때 default 사용
    """
    value = os.getenv(name, default)

    if required and value is None:
        raise ValueError(f"Required environment variable is missing: {name}")

    return value

# @dataclass(frozen=True)
# : [==final] '불변성(Immutability)'을 부여, 
# 객체를 처음 한 번 만들고 나면 그 안의 데이터를 절대 수정할 수 없게 잠가버리는 기능
@dataclass(frozen=True)
class KafkaSettings:
    bootstrap_servers: str
    client_id: str


@dataclass(frozen=True)
class PostgresSettings:
    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass(frozen=True)
class GoogleWorkspaceSettings:
    credentials_path: str
    # 도메인별 token 분리 — 캘린더와 드라이브가 서로 토큰 덮어쓰지 않도록.
    # 각 토큰은 해당 도메인 scope만 가짐.
    token_calendar_path: str
    token_drive_path: str
    token_sheets_path: str
    calendar_id: str


@dataclass(frozen=True)
class StorageSettings:
    base_download_dir: str


@dataclass(frozen=True)
class AppSettings:
    environment: str
    kafka: KafkaSettings
    postgres: PostgresSettings
    google_workspace: GoogleWorkspaceSettings
    storage: StorageSettings


def load_settings() -> AppSettings:
    """
    프로젝트 전체에서 사용할 공통 설정 로더.

    모든 도메인 모듈은 os.getenv를 직접 쓰지 말고,
    이 settings 객체를 통해 설정을 읽도록 한다.
    """

    environment = get_env("APP_ENV", "dev")

    kafka = KafkaSettings(
        bootstrap_servers=get_env("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092"),
        client_id=get_env("KAFKA_CLIENT_ID", "de-pipeline-client"),
    )

    postgres = PostgresSettings(
        host=get_env("POSTGRES_HOST", "localhost"),
        port=int(get_env("POSTGRES_PORT", "5432")),
        database=get_env("POSTGRES_DB", "de_pipeline"),
        user=get_env("POSTGRES_USER", "postgres"),
        password=get_env("POSTGRES_PASSWORD", "postgres"),
    )

    google_workspace = GoogleWorkspaceSettings(
        credentials_path=get_env(
            "GOOGLE_WORKSPACE_CREDENTIALS_PATH",
            str(PROJECT_ROOT / "secrets" / "google" / "google_oauth_client.json"),
        ),
        token_calendar_path=get_env(
            "GOOGLE_WORKSPACE_TOKEN_CALENDAR_PATH",
            str(PROJECT_ROOT / "secrets" / "google" / "token_calendar.json"),
        ),
        token_drive_path=get_env(
            "GOOGLE_WORKSPACE_TOKEN_DRIVE_PATH",
            str(PROJECT_ROOT / "secrets" / "google" / "token_drive.json"),
        ),
        token_sheets_path=get_env(
            "GOOGLE_WORKSPACE_TOKEN_SHEETS_PATH",
            str(PROJECT_ROOT / "secrets" / "google" / "token_sheets.json"),
        ),
        calendar_id=get_env(
            "GOOGLE_CALENDAR_ID",
            "primary",
        ),
    )

    storage = StorageSettings(
        base_download_dir=get_env(
            "GOOGLE_DRIVE_DOWNLOAD_DIR",
            "./data/google_drive",
        ),
    )

    return AppSettings(
        environment=environment,
        kafka=kafka,
        postgres=postgres,
        google_workspace=google_workspace,
        storage=storage,
    )


settings = load_settings()