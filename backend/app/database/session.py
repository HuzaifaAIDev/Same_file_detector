"""
SQLAlchemy engine/session setup.

Works with SQLite out of the box for local development and with
PostgreSQL in production simply by changing DATABASE_URL.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    connect_args = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        future=True,
    )


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. In production, prefer real migrations
    (e.g. Alembic) — this is provided so the app is runnable out of the
    box without extra setup steps."""
    from app.models import comparison, otp, user  # noqa: F401  (register models)

    Base.metadata.create_all(bind=engine)
