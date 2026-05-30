"""Concurrency tests for row-level locking and booking integrity."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from app.extensions import db
from app.services import BookingManager
from app.models import Seat, Booking


def _book_in_context(app, seat_id, user_id):
    with app.app_context():
        return BookingManager.book_seat(seat_id, user_id)


def _cancel_in_context(app, booking_id):
    with app.app_context():
        return BookingManager.cancel_booking(booking_id)


def test_50_concurrent_bookings_one_success(app, single_seat_event):
    seat_id = single_seat_event['seat_id']
    results = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [
            executor.submit(_book_in_context, app, seat_id, f'user_{i}@test.com')
            for i in range(50)
        ]
        for future in as_completed(futures):
            results.append(future.result())

    successes = [r for r in results if r[0] is True and r[3] == 201]
    conflicts = [r for r in results if r[3] == 409]

    assert len(successes) == 1
    assert len(conflicts) == 49

    with app.app_context():
        assert Booking.query.filter_by(seat_id=seat_id).count() == 1
        assert Seat.query.get(seat_id).status == 'BOOKED'


def test_51_concurrent_bookings_one_success(app, single_seat_event):
    seat_id = single_seat_event['seat_id']
    results = []

    with ThreadPoolExecutor(max_workers=51) as executor:
        futures = [
            executor.submit(_book_in_context, app, seat_id, f'user_{i}@test.com')
            for i in range(51)
        ]
        for future in as_completed(futures):
            results.append(future.result())

    successes = [r for r in results if r[0] is True and r[3] == 201]
    conflicts = [r for r in results if r[3] == 409]

    assert len(successes) == 1
    assert len(conflicts) == 50

    with app.app_context():
        assert Booking.query.filter_by(seat_id=seat_id).count() == 1


def test_concurrent_cancellation_no_duplicate(app, single_seat_event):
    seat_id = single_seat_event['seat_id']

    with app.app_context():
        ok, _, booking, _ = BookingManager.book_seat(seat_id, 'cancel-test@test.com')
        assert ok is True
        booking_id = booking['id']

    results = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(_cancel_in_context, app, booking_id),
            executor.submit(_cancel_in_context, app, booking_id),
        ]
        for future in as_completed(futures):
            results.append(future.result())

    success_cancels = [r for r in results if r[0] is True]
    failed_cancels = [r for r in results if r[0] is False]

    assert len(success_cancels) == 1
    assert len(failed_cancels) == 1
    assert any(r[3] == 404 for r in results if not r[0])

    with app.app_context():
        db.session.expire_all()
        assert Booking.query.filter_by(id=booking_id).count() == 0
        assert Seat.query.get(seat_id).status == 'AVAILABLE'


def test_booking_after_cancellation_succeeds(app, single_seat_event):
    seat_id = single_seat_event['seat_id']

    with app.app_context():
        ok, _, booking, _ = BookingManager.book_seat(seat_id, 'round1@test.com')
        assert ok is True
        BookingManager.cancel_booking(booking['id'])

    result = _book_in_context(app, seat_id, 'round2@test.com')
    assert result[0] is True
    assert result[3] == 201

    with app.app_context():
        assert Seat.query.get(seat_id).status == 'BOOKED'
        assert Booking.query.filter_by(seat_id=seat_id).count() == 1
