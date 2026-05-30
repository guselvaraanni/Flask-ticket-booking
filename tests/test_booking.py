"""Booking API and service tests."""

from app.services import BookingManager
from app.models import Seat, Booking


def test_book_seat_success(app, single_seat_event):
    seat_id = single_seat_event['seat_id']

    with app.app_context():
        ok, msg, data, code = BookingManager.book_seat(seat_id, 'alice@test.com')

        assert ok is True
        assert code == 201
        assert data['seat_id'] == seat_id

        seat = Seat.query.get(seat_id)
        assert seat.status == 'BOOKED'
        assert Booking.query.filter_by(seat_id=seat_id).count() == 1


def test_book_seat_conflict(app, single_seat_event):
    seat_id = single_seat_event['seat_id']

    with app.app_context():
        BookingManager.book_seat(seat_id, 'alice@test.com')
        ok, msg, data, code = BookingManager.book_seat(seat_id, 'bob@test.com')

        assert ok is False
        assert code == 409
        assert Booking.query.filter_by(seat_id=seat_id).count() == 1


def test_book_via_api(client, single_seat_event):
    seat_id = single_seat_event['seat_id']

    res = client.post(
        '/api/bookings',
        json={'seat_id': seat_id, 'user_id': 'api-user@test.com'},
    )

    assert res.status_code == 201
    body = res.get_json()
    assert 'booking' in body
    assert body['booking']['seat_id'] == seat_id


def test_cancel_and_rebook(app, single_seat_event):
    seat_id = single_seat_event['seat_id']

    with app.app_context():
        ok, _, booking, _ = BookingManager.book_seat(seat_id, 'first@test.com')
        assert ok is True

        cancel_ok, _, _, cancel_code = BookingManager.cancel_booking(booking['id'])
        assert cancel_ok is True
        assert cancel_code == 200

        seat = Seat.query.get(seat_id)
        assert seat.status == 'AVAILABLE'

        ok2, _, _, code2 = BookingManager.book_seat(seat_id, 'second@test.com')
        assert ok2 is True
        assert code2 == 201
