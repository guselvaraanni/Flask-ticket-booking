"""
Legacy import shim — use app.database for engine, Base, and sessions.
"""

from app.database import Base, SessionLocal, engine, get_db, init_db

__all__ = ['Base', 'SessionLocal', 'engine', 'get_db', 'init_db']
