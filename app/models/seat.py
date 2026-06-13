from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Seat(Base):
    """Individual seat at an event."""

    __tablename__ = 'seats'
    __table_args__ = (
        UniqueConstraint('event_id', 'seat_number', name='uq_event_seat'),
        Index('ix_event_status', 'event_id', 'status'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey('events.id'), nullable=False, index=True)
    seat_number: Mapped[str] = mapped_column(String(10), nullable=False)
    row_letter: Mapped[str] = mapped_column(String(2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='AVAILABLE', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    event = relationship('Event', back_populates='seats')
    bookings = relationship('Booking', back_populates='seat', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'seat_number': self.seat_number,
            'row_letter': self.row_letter,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
        }
