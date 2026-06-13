import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg2://booking_user:booking_pass@localhost:5432/booking_db',
    )
    APP_ENV = os.getenv('APP_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'true').lower() in ('1', 'true', 'yes')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '8000'))


class TestingConfig(Config):
    """Testing configuration (in-memory SQLite)."""

    DATABASE_URL = 'sqlite:///:memory:'
    TESTING = True


config_by_name = {
    'development': Config,
    'testing': TestingConfig,
    'production': Config,
    'default': Config,
}
