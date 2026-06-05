from sqlalchemy.orm import declarative_base


Base = declarative_base()
"""
프로젝트 공용 SQLAlchemy Declarative Base.

모든 ORM 모델은 이 Base를 상속해서 정의한다.
공용 metadata를 공유하므로 Base.metadata.create_all(engine) 으로
한 번에 테이블 생성/삭제가 가능하다.

SQLAlchemy 1.4 호환: declarative_base() 함수형 사용.
1.4.39+ 부터 Mapped / mapped_column 타입 힌트 스타일도 지원.

Usage (1.4 클래식):
    from sqlalchemy import Column, String
    from app.common.db_core import Base

    class CalendarEvent(Base):
        __tablename__ = "calendar_event"

        id = Column(String, primary_key=True)
        summary = Column(String, nullable=True)

Usage (1.4.39+ / 2.0 호환 신 스타일):
    from sqlalchemy.orm import Mapped, mapped_column
    from app.common.db_core import Base

    class CalendarEvent(Base):
        __tablename__ = "calendar_event"

        id: Mapped[str] = mapped_column(primary_key=True)
        summary: Mapped[str | None] = mapped_column(nullable=True)
"""
