"""
UI routes — renders Jinja2 templates. Mutations use existing /api/* endpoints.
"""

from flask import Blueprint, render_template, abort, jsonify
from app.models import Event, Booking, Seat
from app.services import BookingManager

pages_bp = Blueprint('pages', __name__)


def _aggregate_stats():
    events = Event.query.all()
    total_seats = 0
    total_booked = 0
    total_available = 0

    for event in events:
        stats = BookingManager.get_booking_stats(event.id)
        total_seats += stats['total_seats']
        total_booked += stats['booked_seats']
        total_available += stats['available_seats']

    occupancy = (total_booked / total_seats * 100) if total_seats > 0 else 0

    return {
        'total_events': len(events),
        'total_seats': total_seats,
        'total_booked': total_booked,
        'total_available': total_available,
        'occupancy_rate': round(occupancy, 1),
    }


@pages_bp.route('/')
def home():
    summary = _aggregate_stats()
    events = Event.query.order_by(Event.date.asc()).limit(6).all()
    return render_template('index.html', summary=summary, events=events)


@pages_bp.route('/events')
def events_page():
    return render_template('events.html')


@pages_bp.route('/events/<int:event_id>')
def event_detail_page(event_id):
    event = Event.query.get(event_id)
    if not event:
        abort(404)
    stats = BookingManager.get_booking_stats(event_id)
    return render_template('event_detail.html', event=event, stats=stats)


@pages_bp.route('/events/<int:event_id>/book')
def book_page(event_id):
    """Legacy route — redirects to integrated seat map."""
    from flask import redirect, url_for
    return redirect(url_for('pages.event_detail_page', event_id=event_id))


@pages_bp.route('/booking/success')
def booking_success_page():
    return render_template('booking_success.html')


@pages_bp.route('/cancel')
def cancel_page():
    return render_template('cancel.html')


@pages_bp.route('/stats')
def stats_page():
    events = Event.query.order_by(Event.name.asc()).all()
    return render_template('stats.html', events=events)


@pages_bp.route('/stats/<int:event_id>')
def stats_event_page(event_id):
    event = Event.query.get(event_id)
    if not event:
        abort(404)
    stats = BookingManager.get_booking_stats(event_id)
    return render_template('stats.html', events=Event.query.all(), event=event, stats=stats)


@pages_bp.route('/concurrency-demo')
def concurrency_demo_page():
    return render_template('concurrency_demo.html')


@pages_bp.route('/api/ui/booking/<int:booking_id>')
def ui_booking_lookup(booking_id):
    """
    Read-only booking details for the cancel UI (event name, seat number).
    Does not modify booking or concurrency logic.
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    seat = Seat.query.get(booking.seat_id)
    if not seat:
        return jsonify({'error': 'Seat not found'}), 404

    event = Event.query.get(seat.event_id)
    txn = booking.transaction_id or f'TXN-{booking.id:06d}'

    return jsonify({
        'booking': booking.to_dict(),
        'seat_number': seat.seat_number,
        'seat_status': seat.status,
        'event_id': event.id if event else None,
        'event_name': event.name if event else 'Unknown event',
        'event_location': event.location if event else '',
        'ticket_price': event.ticket_price if event else 0,
        'transaction_display': txn,
        'status_label': 'Active' if seat.status == 'BOOKED' else 'Released',
    }), 200
