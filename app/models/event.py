from datetime import datetime
from app.extensions import db

class Event(db.Model):
    """Event model - represents concerts, shows, movies, etc."""
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    ticket_price = db.Column(db.Float, default=25.0)
    category = db.Column(db.String(50), default='general')
    total_seats = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    seats = db.relationship('Seat', backref='event', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Event {self.name}>'

    def to_dict(self):
        """Convert event to dictionary"""
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
