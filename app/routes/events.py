from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event, Seat

router = APIRouter(prefix='/api/events', tags=['events'])


class EventCreate(BaseModel):
    name: str
    date: str
    location: str = ''


class SeatBulkCreate(BaseModel):
    num_rows: int = 10
    seats_per_row: int = 10


@router.post('', status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    try:
        event_date = datetime.fromisoformat(payload.date)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail='Invalid date format. Use ISO format: YYYY-MM-DDTHH:MM:SS',
        )

    event = Event(name=payload.name, date=event_date, location=payload.location)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event.to_dict()


@router.get('')
def list_events(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    return [e.to_dict() for e in events]


@router.get('/{event_id}')
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found')
    return event.to_dict()


@router.post('/{event_id}/seats', status_code=201)
def bulk_create_seats(
    event_id: int, payload: SeatBulkCreate, db: Session = Depends(get_db)
):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found')

    if payload.num_rows <= 0 or payload.seats_per_row <= 0:
        raise HTTPException(
            status_code=400, detail='num_rows and seats_per_row must be positive'
        )

    try:
        for row_idx in range(payload.num_rows):
            row_letter = chr(65 + row_idx)
            for seat_num in range(1, payload.seats_per_row + 1):
                db.add(
                    Seat(
                        event_id=event_id,
                        row_letter=row_letter,
                        seat_number=f'{row_letter}{seat_num}',
                    )
                )
        event.total_seats = payload.num_rows * payload.seats_per_row
        db.commit()
        return {
            'message': f'Created {payload.num_rows * payload.seats_per_row} seats',
            'event_id': event_id,
            'total_seats': event.total_seats,
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f'Failed to create seats: {exc}')


@router.get('/{event_id}/seats')
def list_event_seats(
    event_id: int,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found')

    query = db.query(Seat).filter_by(event_id=event_id)
    if status:
        query = query.filter_by(status=status)
    seats = query.all()
    return [s.to_dict() for s in seats]
