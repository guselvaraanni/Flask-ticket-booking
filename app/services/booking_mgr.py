"""
Booking service — concurrency-safe logic with SELECT ... FOR UPDATE.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Booking, Seat


class BookingManager:
    """Manages seat bookings with PostgreSQL row-level locking."""

    @staticmethod
    def book_seat(session: Session, seat_id: int, user_id: str):
        """
        Book a seat using SELECT ... FOR UPDATE on the seat row.

        PostgreSQL holds the row lock until the transaction commits, preventing
        double booking under concurrent requests.
        """
        try:
            seat = (
                session.query(Seat)
                .with_for_update()
                .filter_by(id=seat_id)
                .first()
            )

            if not seat:
                return False, 'Seat not found', None, 404

            if seat.status == 'BOOKED':
                return False, 'Seat already booked', None, 409

            transaction_id = str(uuid.uuid4())
            booking = Booking(
                seat_id=seat_id,
                user_id=user_id,
                transaction_id=transaction_id,
            )
            seat.status = 'BOOKED'
            session.add(booking)
            session.commit()

            return True, 'Booking successful', booking.to_dict(), 201

        except IntegrityError as exc:
            session.rollback()
            return False, f'Booking failed: {exc}', None, 409
        except Exception as exc:
            session.rollback()
            return False, f'Unexpected error: {exc}', None, 500

    @staticmethod
    def get_booking(session: Session, booking_id: int):
        booking = session.get(Booking, booking_id)
        if not booking:
            return None
        return booking.to_dict()

    @staticmethod
    def cancel_booking(session: Session, booking_id: int):
        try:
            booking = (
                session.query(Booking)
                .with_for_update()
                .filter_by(id=booking_id)
                .first()
            )
            if not booking:
                return False, 'Booking not found', None, 404

            seat = (
                session.query(Seat)
                .with_for_update()
                .filter_by(id=booking.seat_id)
                .first()
            )
            if not seat:
                return False, 'Seat not found', None, 404

            seat.status = 'AVAILABLE'
            session.delete(booking)
            session.commit()

            return True, 'Booking cancelled successfully', None, 200

        except Exception as exc:
            session.rollback()
            return False, f'Failed to cancel booking: {exc}', None, 500

    @staticmethod
    def get_available_seats(session: Session, event_id: int):
        seats = session.query(Seat).filter_by(event_id=event_id, status='AVAILABLE').all()
        return [s.to_dict() for s in seats]

    @staticmethod
    def get_booked_seats(session: Session, event_id: int):
        seats = session.query(Seat).filter_by(event_id=event_id, status='BOOKED').all()
        return [s.to_dict() for s in seats]

    @staticmethod
    def get_booking_stats(session: Session, event_id: int):
        total = session.query(Seat).filter_by(event_id=event_id).count()
        booked = session.query(Seat).filter_by(event_id=event_id, status='BOOKED').count()
        available = total - booked
        return {
            'total_seats': total,
            'booked_seats': booked,
            'available_seats': available,
            'occupancy_rate': (booked / total * 100) if total > 0 else 0,
        }
