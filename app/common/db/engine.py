from __future__ import annotations

import os
from threading import Lock

from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.engine.url import URL

from app.common.config.settings import settings


_engine: Engine | None = None
_engine_pid: int | None = None
_lock = Lock()


def _build_url() -> URL:
    return URL.create(
        drivername="postgresql+psycopg2",
        username=settings.postgres.user,
        password=settings.postgres.password,
        host=settings.postgres.host,
        port=settings.postgres.port,
        database=settings.postgres.database,
    )


def get_engine() -> Engine:
    """
    공용 SQLAlchemy Engine을 반환한다.

    Fork-safe: 자식 프로세스가 부모의 engine(이미 열려있는 TCP socket)을
    그대로 쓰지 않도록, 현재 pid와 engine 생성 시점 pid가 다르면
    engine을 새로 만든다. Airflow LocalExecutor / Celery worker /
    multiprocessing 환경에서 connection 충돌을 피할 수 있다.
    """
    global _engine, _engine_pid

    current_pid = os.getpid()

    if _engine is not None and _engine_pid == current_pid:
        return _engine

    with _lock:
        if _engine is None or _engine_pid != current_pid:
            _engine = create_engine(
                _build_url(),
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                future=True,
            )
            _engine_pid = current_pid

    return _engine


def dispose_engine() -> None:
    """
    현재 프로세스의 engine을 정리한다.
    테스트 teardown이나 명시적 종료 시 호출.
    """
    global _engine, _engine_pid

    if _engine is not None:
        _engine.dispose()
        _engine = None
        _engine_pid = None
