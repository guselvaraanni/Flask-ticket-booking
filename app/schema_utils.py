"""
Ensure presentation-only columns exist on events (UI metadata).
Does not modify booking, seats, or bookings schema used by concurrency logic.
"""

from sqlalchemy import inspect, text
from app.extensions import db


def ensure_event_presentation_columns():
    """Add description, ticket_price, category if missing (MySQL upgrade path)."""
    inspector = inspect(db.engine)
    if 'events' not in inspector.get_table_names():
        return

    existing = {col['name'] for col in inspector.get_columns('events')}
    dialect = db.engine.dialect.name
    statements = []

    if 'description' not in existing:
        statements.append('ALTER TABLE events ADD COLUMN description TEXT NULL')
    if 'ticket_price' not in existing:
        if dialect == 'mysql':
            statements.append(
                'ALTER TABLE events ADD COLUMN ticket_price FLOAT DEFAULT 25.0'
            )
        else:
            statements.append(
                'ALTER TABLE events ADD COLUMN ticket_price FLOAT DEFAULT 25.0'
            )
    if 'category' not in existing:
        if dialect == 'mysql':
            statements.append(
                "ALTER TABLE events ADD COLUMN category VARCHAR(50) DEFAULT 'general'"
            )
        else:
            statements.append(
                "ALTER TABLE events ADD COLUMN category VARCHAR(50) DEFAULT 'general'"
            )

    for stmt in statements:
        db.session.execute(text(stmt))
    if statements:
        db.session.commit()
