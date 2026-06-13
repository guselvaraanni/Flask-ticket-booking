"""
SQLAlchemy engine and session management for FastAPI.
"""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _database_url() -> str:
    return os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg2://booking_user:booking_pass@localhost:5432/booking_db',
    )


def _engine_options() -> dict:
    url = _database_url()
    if url.startswith('sqlite'):
        return {}
    return {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }


engine = create_engine(_database_url(), **_engine_options())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """FastAPI dependency: one session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables and sync presentation columns on events."""
    from app import models  # noqa: F401 — register models
    from app.schema_utils import ensure_event_presentation_columns

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        ensure_event_presentation_columns(session)
