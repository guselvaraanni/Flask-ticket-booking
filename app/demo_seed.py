"""
Demo / portfolio seed data — presentation layer only.
Does not modify booking or concurrency logic.
"""

from datetime import datetime, timedelta
from app.extensions import db
from app.models import Event, Seat, Booking


EVENT_SPECS = [
    {
        'name': 'Movie Night',
        'location': 'Grand Cinema Complex, Hall 1',
        'description': (
            'Premium blockbuster screening with Dolby Atmos sound and reclining seats. '
            'Perfect for demonstrating visual seat selection and instant booking.'
        ),
        'category': 'movie',
        'ticket_price': 499,
        'days_ahead': 5,
        'hour': 19,
        'num_rows': 10,
        'seats_per_row': 10,
    },
    {
        'name': 'Music Concert',
        'location': 'Riverside Amphitheater',
        'description': (
            'Live performance featuring top artists. General admission seating with '
            'a full interactive seat map for high-traffic booking scenarios.'
        ),
        'category': 'concert',
        'ticket_price': 799,
        'days_ahead': 12,
        'hour': 20,
        'num_rows': 10,
        'seats_per_row': 15,
    },
    {
        'name': 'Tech Conference',
        'location': 'Innovation Center, Main Auditorium',
        'description': (
            'Annual developer conference with keynotes and workshops. Reserved seating '
            'showcases concurrency-safe booking under heavy concurrent load.'
        ),
        'category': 'conference',
        'ticket_price': 1999,
        'days_ahead': 21,
        'hour': 9,
        'num_rows': 10,
        'seats_per_row': 20,
    },
]


def _create_seats_for_event(event_id, num_rows, seats_per_row):
    for row_idx in range(num_rows):
        row_letter = chr(65 + row_idx)
        for seat_num in range(1, seats_per_row + 1):
            db.session.add(
                Seat(
                    event_id=event_id,
                    row_letter=row_letter,
                    seat_number=f'{row_letter}{seat_num}',
                    status='AVAILABLE',
                )
            )


def seed_database(reset=False, include_sample_bookings=True):
    """
    Populate the database with portfolio demo events and seats.

    Returns:
        dict: summary of created records
    """
    if reset:
        Booking.query.delete()
        Seat.query.delete()
        Event.query.delete()
        db.session.commit()

    existing = Event.query.filter(
        Event.name.in_([spec['name'] for spec in EVENT_SPECS])
    ).count()
    if existing >= len(EVENT_SPECS) and not reset:
        return {
            'status': 'already_seeded',
            'message': 'Demo events already exist. Use reset=True to reseed.',
            'events': Event.query.count(),
            'seats': Seat.query.count(),
            'bookings': Booking.query.count(),
        }

    if existing > 0 and reset:
        Booking.query.delete()
        Seat.query.delete()
        Event.query.filter(
            Event.name.in_([spec['name'] for spec in EVENT_SPECS])
        ).delete(synchronize_session=False)
        db.session.commit()

    created_events = []

    for spec in EVENT_SPECS:
        if Event.query.filter_by(name=spec['name']).first() and not reset:
            continue

        base = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        event_date = base + timedelta(days=spec['days_ahead'])
        event_date = event_date.replace(hour=spec['hour'])

        event = Event(
            name=spec['name'],
            date=event_date,
            location=spec['location'],
            description=spec['description'],
            ticket_price=spec['ticket_price'],
            category=spec['category'],
            total_seats=spec['num_rows'] * spec['seats_per_row'],
        )
        db.session.add(event)
        db.session.flush()

        _create_seats_for_event(event.id, spec['num_rows'], spec['seats_per_row'])
        created_events.append(event)

    db.session.commit()

    if include_sample_bookings and created_events:
        _seed_sample_bookings(created_events)

    return {
        'status': 'seeded',
        'events': Event.query.count(),
        'seats': Seat.query.count(),
        'bookings': Booking.query.count(),
        'created_event_names': [e.name for e in created_events],
    }


def _seed_sample_bookings(events):
    """A few pre-booked seats so statistics are not empty on first load."""
    from app.services import BookingManager

    targets = [
        ('Movie Night', ['A1', 'A2', 'B5']),
        ('Music Concert', ['C3', 'C4']),
        ('Tech Conference', ['D1']),
    ]

    for event_name, seat_numbers in targets:
        event = Event.query.filter_by(name=event_name).first()
        if not event:
            continue
        for idx, seat_number in enumerate(seat_numbers):
            seat = Seat.query.filter_by(event_id=event.id, seat_number=seat_number).first()
            if not seat or seat.status == 'BOOKED':
                continue
            BookingManager.book_seat(seat.id, f'demo.user{idx}@ticketflow.com')
