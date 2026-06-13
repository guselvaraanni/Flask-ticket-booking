from app.routes.bookings import router as bookings_router
from app.routes.demo import router as demo_router
from app.routes.events import router as events_router
from app.routes.pages import router as pages_router

__all__ = [
    'bookings_router',
    'demo_router',
    'events_router',
    'pages_router',
]
