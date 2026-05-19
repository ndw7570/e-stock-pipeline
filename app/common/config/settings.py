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
    token_path: str
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
        token_path=get_env(
            "GOOGLE_WORKSPACE_TOKEN_PATH",
            str(PROJECT_ROOT / "secrets" / "google" / "token_drive.json"),
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