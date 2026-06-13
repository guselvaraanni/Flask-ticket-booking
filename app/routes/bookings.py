from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import BookingManager

router = APIRouter(prefix='/api/bookings', tags=['bookings'])


class BookingCreate(BaseModel):
    seat_id: int
    user_id: str


@router.post('', status_code=201)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    """Book a seat using PostgreSQL row-level locking (SELECT ... FOR UPDATE)."""
    success, message, booking_data, status_code = BookingManager.book_seat(
        db, payload.seat_id, payload.user_id
    )
    if success:
        return {'message': message, 'booking': booking_data}
    raise HTTPException(status_code=status_code, detail=message)


@router.get('/{booking_id}')
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = BookingManager.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail='Booking not found')
    return booking


@router.delete('/{booking_id}')
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    success, message, _, status_code = BookingManager.cancel_booking(db, booking_id)
    if success:
        return {'message': message}
    raise HTTPException(status_code=status_code, detail=message)


@router.get('/event/{event_id}/available')
def get_available_seats(event_id: int, db: Session = Depends(get_db)):
    seats = BookingManager.get_available_seats(db, event_id)
    return {'event_id': event_id, 'available_seats': seats, 'count': len(seats)}


@router.get('/event/{event_id}/booked')
def get_booked_seats(event_id: int, db: Session = Depends(get_db)):
    seats = BookingManager.get_booked_seats(db, event_id)
    return {'event_id': event_id, 'booked_seats': seats, 'count': len(seats)}


@router.get('/event/{event_id}/stats')
def get_booking_stats(event_id: int, db: Session = Depends(get_db)):
    stats = BookingManager.get_booking_stats(db, event_id)
    return {'event_id': event_id, 'stats': stats}
