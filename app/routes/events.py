from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import db
from app.models import Event, Seat

events_bp = Blueprint('events', __name__, url_prefix='/api/events')

@events_bp.route('', methods=['POST'])
def create_event():
    """ Create a new event """
    data = request.get_json()

    if not data or not data.get('name') or not data.get('date'):
        return jsonify({'error': 'Missing required fields: name, date'}), 400

    try:
        event_date = datetime.fromisoformat(data['date'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format. Use ISO format: YYYY-MM-DDTHH:MM:SS'}), 400

    event = Event(
        name=data['name'],
        date=event_date,
        location=data.get('location', '')
    )

    db.session.add(event)
    db.session.commit()

    return jsonify(event.to_dict()), 201


@events_bp.route('', methods=['GET'])
def list_events():
    """ List all events """
    events = Event.query.all()
    return jsonify([event.to_dict() for event in events]), 200


@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """ Get a specific event by ID """
    event = Event.query.get(event_id)

    if not event:
        return jsonify({'error': 'Event not found'}), 404

    return jsonify(event.to_dict()), 200


@events_bp.route('/<int:event_id>/seats', methods=['POST'])
def bulk_create_seats(event_id):
    """ Bulk create seats for an event.
    Creates seats in format: A1, A2, A3... B1, B2, B3... etc."""
    event = Event.query.get(event_id)

    if not event:
        return jsonify({'error': 'Event not found'}), 404

    data = request.get_json()
    num_rows = data.get('num_rows', 10)
    seats_per_row = data.get('seats_per_row', 10)

    if num_rows <= 0 or seats_per_row <= 0:
        return jsonify({'error': 'num_rows and seats_per_row must be positive'}), 400

    try:
        # Generate seats: A1, A2, ..., B1, B2, etc.
        for row_idx in range(num_rows):
            row_letter = chr(65 + row_idx)  # A, B, C, D, etc.
            for seat_num in range(1, seats_per_row + 1):
                seat = Seat(
                    event_id=event_id,
                    row_letter=row_letter,
                    seat_number=f"{row_letter}{seat_num}"
                )
                db.session.add(seat)

        event.total_seats = num_rows * seats_per_row
        db.session.commit()

        return jsonify({
            'message': f'Created {num_rows * seats_per_row} seats',
            'event_id': event_id,
            'total_seats': event.total_seats
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create seats: {str(e)}'}), 500


@events_bp.route('/<int:event_id>/seats', methods=['GET'])
def list_event_seats(event_id):
    """ List all seats for an event """
    event = Event.query.get(event_id)

    if not event:
        return jsonify({'error': 'Event not found'}), 404

    status_filter = request.args.get('status')
    query = Seat.query.filter_by(event_id=event_id)

    if status_filter:
        query = query.filter_by(status=status_filter)

    seats = query.all()
    return jsonify([seat.to_dict() for seat in seats]), 200
