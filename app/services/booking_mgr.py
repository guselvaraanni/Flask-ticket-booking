"""
Booking Service - Contains the concurrency-safe booking logic
This is where the row-level locking (SELECT ... FOR UPDATE) happens.
"""

from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import Seat, Booking
import uuid

class BookingManager:
    """Manages seat bookings with concurrency-safe locking"""

    @staticmethod
    def book_seat(seat_id, user_id):
        """
        Book a seat for a user with row-level locking.
        
        This method uses MySQL InnoDB SELECT ... FOR UPDATE to lock the seat row,
        preventing race conditions when multiple users try to book the same seat.
        
        Args:
            seat_id (int): The ID of the seat to book
            user_id (str): The user attempting to book the seat
            
        Returns:
            tuple: (success: bool, message: str, booking_data: dict or None, status_code: int)
        """
        try:
            # Query the seat WITH row-level lock
            # with_for_update() locks the row for the duration of the transaction
            seat = Seat.query.with_for_update().filter_by(id=seat_id).first()

            # Check if seat exists
            if not seat:
                return False, "Seat not found", None, 404

            # Check if seat is already booked
            if seat.status == 'BOOKED':
                return False, "Seat already booked", None, 409

            # Create a new booking
            transaction_id = str(uuid.uuid4())
            booking = Booking(
                seat_id=seat_id,
                user_id=user_id,
                transaction_id=transaction_id
            )

            # Update seat status
            seat.status = 'BOOKED'

            # Add and commit
            db.session.add(booking)
            db.session.commit()

            return True, "Booking successful", booking.to_dict(), 201

        except IntegrityError as e:
            db.session.rollback()
            return False, f"Booking failed: {str(e)}", None, 409
        except Exception as e:
            db.session.rollback()
            return False, f"Unexpected error: {str(e)}", None, 500

    @staticmethod
    def get_booking(booking_id):
        """Retrieve a booking by ID"""
        booking = Booking.query.get(booking_id)
        if not booking:
            return None
        return booking.to_dict()

    @staticmethod
    def cancel_booking(booking_id):
        """
        Cancel a booking and release the seat.
        Also uses row-level locking to prevent race conditions.
        """
        try:
            # Lock the booking row first so concurrent cancel requests cannot
            # both pass the existence check and corrupt seat state.
            booking = Booking.query.with_for_update().filter_by(id=booking_id).first()
            if not booking:
                return False, "Booking not found", None, 404

            seat = Seat.query.with_for_update().filter_by(id=booking.seat_id).first()
            
            if not seat:
                return False, "Seat not found", None, 404

            # Release the seat
            seat.status = 'AVAILABLE'
            db.session.delete(booking)
            db.session.commit()

            return True, "Booking cancelled successfully", None, 200

        except Exception as e:
            db.session.rollback()
            return False, f"Failed to cancel booking: {str(e)}", None, 500

    @staticmethod
    def get_available_seats(event_id):
        """Get all available seats for an event"""
        seats = Seat.query.filter_by(event_id=event_id, status='AVAILABLE').all()
        return [seat.to_dict() for seat in seats]

    @staticmethod
    def get_booked_seats(event_id):
        """Get all booked seats for an event"""
        seats = Seat.query.filter_by(event_id=event_id, status='BOOKED').all()
        return [seat.to_dict() for seat in seats]

    @staticmethod
    def get_booking_stats(event_id):
        """Get booking statistics for an event"""
        total = Seat.query.filter_by(event_id=event_id).count()
        booked = Seat.query.filter_by(event_id=event_id, status='BOOKED').count()
        available = total - booked

        return {
            'total_seats': total,
            'booked_seats': booked,
            'available_seats': available,
            'occupancy_rate': (booked / total * 100) if total > 0 else 0
        }
