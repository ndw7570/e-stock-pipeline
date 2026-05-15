from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session, sessionmaker

from app.common.db.engine import get_engine


def _make_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


@contextmanager
def session_scope() -> Iterator[Session]:
    """
    트랜잭션 범위 Session context manager.

    정상 종료 시 자동 commit, 예외 시 자동 rollback, 종료 시 항상 close.

    Usage:
        from app.common.db import session_scope


        with session_scope() as s:
            s.add(some_model_instance)
            # block 종료 시 자동 commit

        with session_scope() as s:
            result = s.execute(select(SomeModel).where(SomeModel.id == 1))
            row = result.scalar_one_or_none()

    주의: Airflow task 안에서 task 단위로 호출. 모듈 전역에서 미리 session을
    만들어 두지 말 것 (fork 후 connection 깨짐).
    """
    session_factory = _make_session_factory()
    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
