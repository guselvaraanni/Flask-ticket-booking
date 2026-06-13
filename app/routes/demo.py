from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.demo_seed import seed_database
from app.models import Booking, Event, Seat

router = APIRouter(prefix='/api/demo', tags=['demo'])


class SeedRequest(BaseModel):
    reset: bool = False
    include_bookings: bool = True


@router.post('/seed')
def seed_demo_data(payload: SeedRequest, db: Session = Depends(get_db)):
    result = seed_database(
        db, reset=payload.reset, include_sample_bookings=payload.include_bookings
    )
    return result


@router.get('/status')
def demo_status(db: Session = Depends(get_db)):
    return {
        'events': db.query(Event).count(),
        'seats': db.query(Seat).count(),
        'bookings': db.query(Booking).count(),
        'ready': db.query(Event).count() >= 3,
    }
