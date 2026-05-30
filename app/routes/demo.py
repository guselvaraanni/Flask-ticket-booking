"""
Demo seed API — populates sample data for UI demonstrations.
Does not modify booking or concurrency services.
"""

from flask import Blueprint, jsonify, request
from app.demo_seed import seed_database

demo_bp = Blueprint('demo', __name__, url_prefix='/api/demo')


@demo_bp.route('/seed', methods=['POST'])
def seed_demo_data():
    """
    Create demo events, seats, and optional sample bookings.
    ---
    parameters:
      - name: body
        in: body
        schema:
          properties:
            reset:
              type: boolean
              example: false
            include_bookings:
              type: boolean
              example: true
    responses:
      200:
        description: Seed result summary
    """
    data = request.get_json(silent=True) or {}
    reset = bool(data.get('reset', False))
    include_bookings = bool(data.get('include_bookings', True))

    result = seed_database(reset=reset, include_sample_bookings=include_bookings)
    return jsonify(result), 200


@demo_bp.route('/status', methods=['GET'])
def demo_status():
    """Return current database counts for the demo UI."""
    from app.models import Event, Seat, Booking

    return jsonify({
        'events': Event.query.count(),
        'seats': Seat.query.count(),
        'bookings': Booking.query.count(),
        'ready': Event.query.count() >= 3,
    }), 200
