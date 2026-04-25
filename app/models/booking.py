from datetime import datetime
from app.extensions import db

class Booking(db.Model):
    """Booking model - represents a confirmed seat booking"""
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False, unique=True, index=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)  # In real app, would FK to users
    booking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_id = db.Column(db.String(255), unique=True, nullable=True)

    def __repr__(self):
        return f'<Booking seat_id={self.seat_id}, user_id={self.user_id}>'

    def to_dict(self):
        """Convert booking to dictionary"""
        return {
            'id': self.id,
            'seat_id': self.seat_id,
            'user_id': self.user_id,
            'booking_timestamp': self.booking_timestamp.isoformat(),
            'transaction_id': self.transaction_id,
        }
