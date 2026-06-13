"""
FastAPI application factory.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes import (
    bookings_router,
    demo_router,
    events_router,
    pages_router,
)

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv('TESTING', '').lower() not in ('1', 'true', 'yes'):
        init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title='TicketFlow — Seat Booking API',
        description='Concurrency-safe ticket booking with PostgreSQL row-level locking',
        version='2.0.0',
        docs_url='/docs',
        redoc_url='/redoc',
        lifespan=lifespan,
    )

    app.mount(
        '/static',
        StaticFiles(directory=os.path.join(_ROOT, 'static')),
        name='static',
    )

    app.include_router(pages_router)
    app.include_router(events_router)
    app.include_router(bookings_router)
    app.include_router(demo_router)

    @app.get('/health', tags=['system'])
    def health():
        return {'status': 'healthy', 'message': 'API is running'}

    @app.get('/api', tags=['system'])
    def api_index():
        return {
            'message': 'Welcome to the Seat Booking API',
            'docs': '/docs',
            'ui': '/',
            'version': '2.0.0',
        }

    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        if request.url.path.startswith('/api'):
            return JSONResponse({'error': 'Resource not found'}, status_code=404)
        return JSONResponse({'error': 'Resource not found'}, status_code=404)

    return app


app = create_app()
