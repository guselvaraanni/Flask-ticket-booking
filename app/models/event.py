from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Event(Base):
    """Event model — concerts, shows, movies, etc."""

    __tablename__ = 'events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ticket_price: Mapped[float] = mapped_column(Float, default=25.0)
    category: Mapped[str] = mapped_column(String(50), default='general')
    total_seats: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    seats = relationship('Seat', back_populates='event', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date.isoformat(),
            'location': self.location,
            'description': self.description,
            'ticket_price': self.ticket_price,
            'category': self.category,
            'total_seats': self.total_seats,
            'created_at': self.created_at.isoformat(),
        }
