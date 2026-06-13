"""Pytest fixtures for TicketFlow (FastAPI + in-memory SQLite)."""

import os

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ['TESTING'] = 'true'

from app.database import Base, get_db
from app.main import create_app
from app.models import Event, Seat


@pytest.fixture
def test_engine():
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session_factory(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def api_app(session_factory):
    """FastAPI app (named api_app to avoid pytest-flask hook on 'app')."""
    application = create_app()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(api_app):
    return TestClient(api_app)


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def single_seat_event(db_session):
    event = Event(
        name='Test Event',
        date=datetime.utcnow() + timedelta(days=7),
        location='Test Hall',
        description='Concurrency test event',
        ticket_price=10.0,
        category='movie',
        total_seats=1,
    )
    db_session.add(event)
    db_session.flush()

    seat = Seat(
        event_id=event.id,
        row_letter='A',
        seat_number='A1',
        status='AVAILABLE',
    )
    db_session.add(seat)
    db_session.commit()

    return {'event_id': event.id, 'seat_id': seat.id}
