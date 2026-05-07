from flask import Blueprint, request, jsonify
from app.services import BookingManager
from app.models import Booking

bookings_bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')

@bookings_bp.route('', methods=['POST'])
def create_booking():
    """
    Book a specific seat for a user.
    
    This endpoint uses PostgreSQL's SELECT ... FOR UPDATE (row-level locking)
    to prevent race conditions. Only one user can book a seat at a time.
    
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            seat_id:
              type: integer
              example: 1
            user_id:
              type: string
              example: "user@example.com"
    responses:
      201:
        description: Booking successful
      409:
        description: Seat already booked (conflict)
      404:
        description: Seat not found
      400:
        description: Bad request
    """
    data = request.get_json()

    if not data or not data.get('seat_id') or not data.get('user_id'):
        return jsonify({'error': 'Missing required fields: seat_id, user_id'}), 400

    seat_id = data.get('seat_id')
    user_id = data.get('user_id')

    # Call the booking service with row-level locking
    success, message, booking_data, status_code = BookingManager.book_seat(seat_id, user_id)

    if success:
        return jsonify({
            'message': message,
            'booking': booking_data
        }), status_code
    else:
        return jsonify({'error': message}), status_code


@bookings_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    """
    Retrieve a booking by ID.
    ---
    parameters:
      - name: booking_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Booking details
      404:
        description: Booking not found
    """
    booking = BookingManager.get_booking(booking_id)

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    return jsonify(booking), 200


@bookings_bp.route('/<int:booking_id>', methods=['DELETE'])
def cancel_booking(booking_id):
    """
    Cancel a booking and release the seat back to AVAILABLE.
    ---
    parameters:
      - name: booking_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Booking cancelled
      404:
        description: Booking not found
    """
    success, message, _, status_code = BookingManager.cancel_booking(booking_id)

    if success:
        return jsonify({'message': message}), status_code
    else:
        return jsonify({'error': message}), status_code


@bookings_bp.route('/event/<int:event_id>/available', methods=['GET'])
def get_available_seats(event_id):
    """
    Get all available seats for an event.
    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: List of available seats
    """
    seats = BookingManager.get_available_seats(event_id)
    return jsonify({
        'event_id': event_id,
        'available_seats': seats,
        'count': len(seats)
    }), 200


@bookings_bp.route('/event/<int:event_id>/booked', methods=['GET'])
def get_booked_seats(event_id):
    """
    Get all booked seats for an event.
    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: List of booked seats
    """
    seats = BookingManager.get_booked_seats(event_id)
    return jsonify({
        'event_id': event_id,
        'booked_seats': seats,
        'count': len(seats)
    }), 200


@bookings_bp.route('/event/<int:event_id>/stats', methods=['GET'])
def get_booking_stats(event_id):
    """
    Get booking statistics for an event.
    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Booking statistics
    """
    stats = BookingManager.get_booking_stats(event_id)
    return jsonify({
        'event_id': event_id,
        'stats': stats
    }), 200
