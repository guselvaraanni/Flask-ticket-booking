"""Booking API and service tests."""

from app.models import Booking, Seat
from app.services import BookingManager


def test_book_seat_success(db_session, single_seat_event):
    seat_id = single_seat_event['seat_id']

    ok, msg, data, code = BookingManager.book_seat(db_session, seat_id, 'alice@test.com')

    assert ok is True
    assert code == 201
    assert data['seat_id'] == seat_id

    seat = db_session.get(Seat, seat_id)
    assert seat.status == 'BOOKED'
    assert db_session.query(Booking).filter_by(seat_id=seat_id).count() == 1


def test_book_seat_conflict(db_session, single_seat_event):
    seat_id = single_seat_event['seat_id']

    BookingManager.book_seat(db_session, seat_id, 'alice@test.com')
    ok, msg, data, code = BookingManager.book_seat(db_session, seat_id, 'bob@test.com')

    assert ok is False
    assert code == 409
    assert db_session.query(Booking).filter_by(seat_id=seat_id).count() == 1


def test_book_via_api(client, single_seat_event):
    seat_id = single_seat_event['seat_id']

    res = client.post(
        '/api/bookings',
        json={'seat_id': seat_id, 'user_id': 'api-user@test.com'},
    )

    assert res.status_code == 201
    body = res.json()
    assert 'booking' in body
    assert body['booking']['seat_id'] == seat_id


def test_cancel_and_rebook(db_session, single_seat_event):
    seat_id = single_seat_event['seat_id']

    ok, _, booking, _ = BookingManager.book_seat(db_session, seat_id, 'first@test.com')
    assert ok is True

    cancel_ok, _, _, cancel_code = BookingManager.cancel_booking(db_session, booking['id'])
    assert cancel_ok is True
    assert cancel_code == 200

    seat = db_session.get(Seat, seat_id)
    assert seat.status == 'AVAILABLE'

    ok2, _, _, code2 = BookingManager.book_seat(db_session, seat_id, 'second@test.com')
    assert ok2 is True
    assert code2 == 201
