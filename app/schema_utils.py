"""
Ensure presentation-only columns exist on events (UI metadata).
"""

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session


def ensure_event_presentation_columns(session: Session) -> None:
    """Add description, ticket_price, category if missing (PostgreSQL upgrade path)."""
    inspector = inspect(session.get_bind())
    if 'events' not in inspector.get_table_names():
        return

    existing = {col['name'] for col in inspector.get_columns('events')}
    statements = []

    if 'description' not in existing:
        statements.append('ALTER TABLE events ADD COLUMN description TEXT NULL')
    if 'ticket_price' not in existing:
        statements.append(
            'ALTER TABLE events ADD COLUMN ticket_price DOUBLE PRECISION DEFAULT 25.0'
        )
    if 'category' not in existing:
        statements.append(
            "ALTER TABLE events ADD COLUMN category VARCHAR(50) DEFAULT 'general'"
        )

    for stmt in statements:
        session.execute(text(stmt))
    if statements:
        session.commit()
