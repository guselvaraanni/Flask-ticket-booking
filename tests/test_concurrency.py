"""Concurrency tests for row-level locking and booking integrity."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from app.models import Booking, Seat
from app.services import BookingManager


def _book_with_session(session_factory, seat_id, user_id):
    session = session_factory()
    try:
        return BookingManager.book_seat(session, seat_id, user_id)
    finally:
        session.close()


def _cancel_with_session(session_factory, booking_id):
    session = session_factory()
    try:
        return BookingManager.cancel_booking(session, booking_id)
    finally:
        session.close()


def _assert_single_booking(session_factory, seat_id):
    session = session_factory()
    try:
        assert session.query(Booking).filter_by(seat_id=seat_id).count() == 1
        assert session.get(Seat, seat_id).status == 'BOOKED'
    finally:
        session.close()


def test_50_concurrent_bookings_one_success(session_factory, single_seat_event):
    seat_id = single_seat_event['seat_id']
    results = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [
            executor.submit(
                _book_with_session, session_factory, seat_id, f'user_{i}@test.com'
            )
            for i in range(50)
        ]
        for future in as_completed(futures):
            results.append(future.result())

    successes = [r for r in results if r[0] is True and r[3] == 201]
    assert len(successes) <= 1
    _assert_single_booking(session_factory, seat_id)


def test_51_concurrent_bookings_one_success(session_factory, single_seat_event):
    seat_id = single_seat_event['seat_id']
    results = []

    with ThreadPoolExecutor(max_workers=51) as executor:
        futures = [
            executor.submit(
                _book_with_session, session_factory, seat_id, f'user_{i}@test.com'
            )
            for i in range(51)
        ]
        for future in as_completed(futures):
            results.append(future.result())

    successes = [r for r in results if r[0] is True and r[3] == 201]
    assert len(successes) <= 1
    _assert_single_booking(session_factory, seat_id)


def test_concurrent_cancellation_no_duplicate(session_factory, single_seat_event):
    seat_id = single_seat_event['seat_id']
    session = session_factory()
    try:
        ok, _, booking, _ = BookingManager.book_seat(
            session, seat_id, 'cancel-test@test.com'
        )
        assert ok is True
        booking_id = booking['id']
    finally:
        session.close()

    results = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(_cancel_with_session, session_factory, booking_id),
            executor.submit(_cancel_with_session, session_factory, booking_id),
        ]
        for future in as_completed(futures):
            results.append(future.result())

    success_cancels = [r for r in results if r[0] is True]

    assert len(success_cancels) >= 1

    session = session_factory()
    try:
        assert session.query(Booking).filter_by(id=booking_id).count() == 0
        assert session.get(Seat, seat_id).status == 'AVAILABLE'
    finally:
        session.close()


def test_booking_after_cancellation_succeeds(session_factory, single_seat_event):
    seat_id = single_seat_event['seat_id']
    session = session_factory()
    try:
        ok, _, booking, _ = BookingManager.book_seat(session, seat_id, 'round1@test.com')
        assert ok is True
        BookingManager.cancel_booking(session, booking['id'])
    finally:
        session.close()

    result = _book_with_session(session_factory, seat_id, 'round2@test.com')
    assert result[0] is True
    assert result[3] == 201

    session = session_factory()
    try:
        assert session.get(Seat, seat_id).status == 'BOOKED'
        assert session.query(Booking).filter_by(seat_id=seat_id).count() == 1
    finally:
        session.close()
