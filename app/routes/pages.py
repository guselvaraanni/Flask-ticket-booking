"""
UI routes — Jinja2 HTML pages. Mutations use /api/* JSON endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking, Event, Seat
from app.services import BookingManager
from app.templating import templates

router = APIRouter(tags=['pages'])


def _aggregate_stats(db: Session):
    events = db.query(Event).all()
    total_seats = total_booked = total_available = 0

    for event in events:
        stats = BookingManager.get_booking_stats(db, event.id)
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


def _render(request: Request, name: str, active_page: str, **ctx):
    return templates.TemplateResponse(
        name,
        {'request': request, 'active_page': active_page, **ctx},
    )


@router.get('/', response_class=HTMLResponse, name='home')
def home(request: Request, db: Session = Depends(get_db)):
    summary = _aggregate_stats(db)
    events = db.query(Event).order_by(Event.date.asc()).limit(6).all()
    return _render(request, 'index.html', 'home', summary=summary, events=events)


@router.get('/events', response_class=HTMLResponse, name='events')
def events_page(request: Request):
    return _render(request, 'events.html', 'events')


@router.get('/events/{event_id}', response_class=HTMLResponse, name='event_detail')
def event_detail_page(event_id: int, request: Request, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found')
    stats = BookingManager.get_booking_stats(db, event_id)
    return _render(
        request, 'event_detail.html', 'events', event=event, stats=stats
    )


@router.get('/events/{event_id}/book', name='book_redirect')
def book_page(event_id: int):
    return RedirectResponse(url=f'/events/{event_id}', status_code=302)


@router.get('/booking/success', response_class=HTMLResponse, name='booking_success')
def booking_success_page(request: Request):
    return _render(request, 'booking_success.html', 'booking_success')


@router.get('/cancel', response_class=HTMLResponse, name='cancel')
def cancel_page(request: Request):
    return _render(request, 'cancel.html', 'cancel')


@router.get('/stats', response_class=HTMLResponse, name='stats')
def stats_page(request: Request, db: Session = Depends(get_db)):
    events = db.query(Event).order_by(Event.name.asc()).all()
    return _render(request, 'stats.html', 'stats', events=events)


@router.get('/stats/{event_id}', response_class=HTMLResponse, name='stats_event')
def stats_event_page(event_id: int, request: Request, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found')
    stats = BookingManager.get_booking_stats(db, event_id)
    events = db.query(Event).order_by(Event.name.asc()).all()
    return _render(
        request,
        'stats.html',
        'stats',
        events=events,
        event=event,
        stats=stats,
    )


@router.get('/concurrency-demo', response_class=HTMLResponse, name='concurrency_demo')
def concurrency_demo_page(request: Request):
    return _render(request, 'concurrency_demo.html', 'concurrency_demo')


@router.get('/api/ui/booking/{booking_id}')
def ui_booking_lookup(booking_id: int, db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail='Booking not found')

    seat = db.get(Seat, booking.seat_id)
    if not seat:
        raise HTTPException(status_code=404, detail='Seat not found')

    event = db.get(Event, seat.event_id)
    txn = booking.transaction_id or f'TXN-{booking.id:06d}'

    return {
        'booking': booking.to_dict(),
        'seat_number': seat.seat_number,
        'seat_status': seat.status,
        'event_id': event.id if event else None,
        'event_name': event.name if event else 'Unknown event',
        'event_location': event.location if event else '',
        'ticket_price': event.ticket_price if event else 0,
        'transaction_display': txn,
        'status_label': 'Active' if seat.status == 'BOOKED' else 'Released',
    }
