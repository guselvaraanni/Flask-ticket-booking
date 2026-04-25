from datetime import datetime
from app.extensions import db

class Seat(db.Model):
    """Seat model - represents individual seats at an event"""
    __tablename__ = 'seats'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False, index=True)
    seat_number = db.Column(db.String(10), nullable=False)  # e.g., "A1", "A2"
    row_letter = db.Column(db.String(2), nullable=False)    # e.g., "A", "B"
    status = db.Column(db.String(20), default='AVAILABLE', nullable=False)  # AVAILABLE, BOOKED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite index for uniqueness per event
    __table_args__ = (
        db.UniqueConstraint('event_id', 'seat_number', name='uq_event_seat'),
        db.Index('ix_event_status', 'event_id', 'status'),
    )

    # Relationships
    bookings = db.relationship('Booking', backref='seat', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Seat {self.seat_number}>'

    def to_dict(self):
        """Convert seat to dictionary"""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'seat_number': self.seat_number,
            'row_letter': self.row_letter,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
        }
