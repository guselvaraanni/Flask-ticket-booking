"""Pytest fixtures for TicketFlow."""

import pytest
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import Event, Seat


@pytest.fixture
def app():
    """Flask app with in-memory SQLite for isolated tests."""
    application = create_app('testing')
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def single_seat_event(app):
    """One event with a single available seat."""
    with app.app_context():
        event = Event(
            name='Test Event',
            date=datetime.utcnow() + timedelta(days=7),
            location='Test Hall',
            description='Concurrency test event',
            ticket_price=10.0,
            category='movie',
            total_seats=1,
        )
        db.session.add(event)
        db.session.flush()

        seat = Seat(
            event_id=event.id,
            row_letter='A',
            seat_number='A1',
            status='AVAILABLE',
        )
        db.session.add(seat)
        db.session.commit()

        return {
            'event_id': event.id,
            'seat_id': seat.id,
        }
