from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Booking(Base):
    """Confirmed seat booking."""

    __tablename__ = 'bookings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seat_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('seats.id'), nullable=False, unique=True, index=True
    )
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    booking_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)

    seat = relationship('Seat', back_populates='bookings')

    def to_dict(self):
        return {
            'id': self.id,
            'seat_id': self.seat_id,
            'user_id': self.user_id,
            'booking_timestamp': self.booking_timestamp.isoformat(),
            'transaction_id': self.transaction_id,
        }
