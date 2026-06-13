# TicketFlow — Concurrency-Safe Ticket Booking Platform

**Concurrency-Safe Ticketing System | Python, FastAPI, PostgreSQL, Threading**

A full-stack seat booking application with a production-style web UI and a concurrency-safe REST API. Multiple users can attempt to book the same seat at the same time; **PostgreSQL row-level locking** (`SELECT ... FOR UPDATE`) ensures exactly one booking succeeds.

![TicketFlow Home](screenshots/Screenshot%202026-05-30%20132932.png)

---

## Project Overview

### What problem does this solve?

In high-traffic ticketing (concerts, movies, conferences), many users often click **Book** on the same seat within milliseconds. Without proper synchronization, two requests can both see the seat as available and both commit—causing **double bookings** and inconsistent inventory.

**TicketFlow** solves this with:

- **Database-level row locks** (`SELECT ... FOR UPDATE`) before checking or updating seat status
- **ACID transactions** on PostgreSQL
- A **unique constraint** on `bookings.seat_id` as a safety net
- Automated **concurrency and load tests** (pytest + `ThreadPoolExecutor`)

### Why concurrency-safe booking matters

Race conditions are invisible in single-user demos but appear immediately under real load. This project demonstrates **correct behavior under contention**—the same data-layer guarantees expected from production ticketing platforms.

### Technology stack

| Layer | Technologies |
|--------|----------------|
| **Frontend** | HTML5, Jinja2 templates, vanilla CSS, vanilla JavaScript |
| **Backend** | Python 3.9+, **FastAPI**, Uvicorn, Pydantic |
| **ORM** | **SQLAlchemy 2.x** (session-per-request via `Depends(get_db)`) |
| **Database** | **PostgreSQL 14+**, psycopg2 driver |
| **API docs** | FastAPI auto-generated OpenAPI at `/docs` |
| **Testing** | pytest, httpx/TestClient, `ThreadPoolExecutor` load script |

> **Note:** The API uses **synchronous** route handlers and SQLAlchemy sessions (not async SQLAlchemy). Concurrency is enforced by **PostgreSQL transactions and row locks**, not by async I/O.

---

## Features

| Feature | Description |
|---------|-------------|
| **Event management** | Create/list events via API; browse in UI with category banners |
| **Movie-style seat selection** | Interactive cinema grid, color-coded availability |
| **Real-time availability** | Live seat map and stats from `/api/events` and `/api/bookings` |
| **Booking confirmation** | Digital ticket with Booking ID, transaction UUID, print/download |
| **Cancellation** | Search by Booking ID, modal confirm, seat returns to `AVAILABLE` |
| **Statistics dashboard** | Global and per-event occupancy with bar charts |
| **Demo data loader** | `python seed_data.py` or `POST /api/demo/seed` |
| **Concurrency protection** | `BookingManager` uses `with_for_update()` on book and cancel |
| **PostgreSQL integration** | `postgresql+psycopg2://` connection pooling |
| **Responsive UI** | Mobile-first CSS, hamburger nav, contained seat-map scroll |

---

## Architecture

### Request flow (FastAPI)

```
Browser / Client
      │
      ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Uvicorn   │────▶│  FastAPI app     │────▶│  API routers    │
│  (ASGI)     │     │  app/main.py     │     │  events,        │
└─────────────┘     └────────┬─────────┘     │  bookings, demo │
                             │               └────────┬────────┘
                             │                        │
                             ▼                        ▼
                    ┌────────────────┐     ┌─────────────────────┐
                    │  pages router  │     │  BookingManager     │
                    │  (Jinja2 HTML) │     │  (services layer)   │
                    └────────────────┘     └──────────┬──────────┘
                                                      │
                                                      ▼
                                           ┌─────────────────────┐
                                           │  SQLAlchemy Session │
                                           │  SELECT ... FOR     │
                                           │  UPDATE + COMMIT    │
                                           └──────────┬──────────┘
                                                      ▼
                                           ┌─────────────────────┐
                                           │     PostgreSQL      │
                                           └─────────────────────┘
```

### Frontend

| Component | Role |
|-----------|------|
| **Jinja2** | Server-rendered pages in `templates/` |
| **CSS / JS** | `static/css/style.css`, `static/js/app.js` |
| **API calls** | UI mutations go to `/api/*` JSON endpoints |

### Backend

| Component | Role |
|-----------|------|
| **FastAPI** | App factory `create_app()` in `app/main.py` |
| **Routers** | `app/routes/events.py`, `bookings.py`, `pages.py`, `demo.py` |
| **Services** | `app/services/booking_mgr.py` — booking/cancel logic |
| **Database** | `app/database.py` — engine, `SessionLocal`, `get_db()` |

### Database tables

| Table | Purpose |
|-------|---------|
| **events** | Name, date, location, description, price, category, `total_seats` |
| **seats** | `event_id`, `seat_number`, `row_letter`, `status` (`AVAILABLE` / `BOOKED`) |
| **bookings** | `seat_id` (UNIQUE), `user_id`, `transaction_id`, timestamp |

### Concurrency layer

```
Client A ──POST /api/bookings──┐
                               ├──► BEGIN (implicit)
Client B ──POST /api/bookings──┘         │
                                         ▼
                          SELECT ... FOR UPDATE (seat row)
                                         │
              ┌──────────────────────────┴──────────────────────────┐
              ▼                                                     ▼
        First transaction                                      Second waits
        seat AVAILABLE → BOOKED + INSERT                       then sees BOOKED
        COMMIT → 201                                             → 409 Conflict
```

| Mechanism | Implementation |
|-----------|----------------|
| **Row-level locking** | `session.query(Seat).with_for_update().filter_by(id=seat_id)` |
| **Transaction isolation** | One SQLAlchemy session per request; `commit()` / `rollback()` |
| **Unique constraint** | `bookings.seat_id` UNIQUE |
| **Cancel safety** | `FOR UPDATE` on booking + seat rows in `cancel_booking()` |
| **Load validation** | 51 concurrent HTTP requests; exactly 1× `201` |

---

## Application screenshots

Screenshots are in [`screenshots/`](screenshots/), ordered by user journey.

### 1. Home page

![Home page — hero and live statistics](screenshots/Screenshot%202026-05-30%20132932.png)

Landing page with hero, live stats, and links to browse events or learn how concurrency is enforced.

### 2. Events listing

![Events listing](screenshots/Screenshot%202026-05-30%20133008.png)

Browse Movie Night, Music Concert, and Tech Conference with INR pricing and availability.

### 3. Home — featured events

![Home page — featured events](screenshots/Screenshot%202026-05-30%20132954.png)

Featured events and trust cards describing row-level locking and load testing.

### 4–6. Seat selection and booking

![Seat selection and booking panel](screenshots/Screenshot%202026-05-30%20133054.png)

Cinema seat map with **FastAPI**-backed live availability; inline booking form posts to `POST /api/bookings`.

### 7. Booking success

![Booking success — digital ticket](screenshots/Screenshot%202026-05-30%20133107.png)

Confirmed ticket with transaction UUID stored in **PostgreSQL**.

![Print ticket preview](screenshots/Screenshot%202026-05-30%20133123.png)

### 8. Statistics dashboard

![Statistics dashboard](screenshots/Screenshot%202026-05-30%20133144.png)

Live occupancy from `/api/bookings/event/{id}/stats`.

### 9. Cancellation

![Cancel booking — details](screenshots/Screenshot%202026-05-30%20133203.png)

![Cancel booking — confirmation modal](screenshots/Screenshot%202026-05-30%20133215.png)

![Cancel booking — success](screenshots/Screenshot%202026-05-30%20133226.png)

### 10. How it works (concurrency demo)

![Concurrency demo](screenshots/Screenshot%202026-05-30%20133306.png)

![Concurrent booking flow](screenshots/Screenshot%202026-05-30%20133322.png)

Explains PostgreSQL `SELECT ... FOR UPDATE`, unique constraints, and `tests/simulate_load.py`.

### 11. Responsive UI

The UI is responsive from **320px–1920px**. Test with browser DevTools or a mobile device against `http://localhost:8000`.

---

## API summary

Interactive docs: **http://localhost:8000/docs**

### System

| Method | Endpoint | Response |
|--------|----------|----------|
| GET | `/health` | `{ "status": "healthy" }` |
| GET | `/api` | API metadata + links |

### Events — `/api/events`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/events` | Create event |
| GET | `/api/events` | List events |
| GET | `/api/events/{id}` | Get event |
| POST | `/api/events/{id}/seats` | Bulk create seats |
| GET | `/api/events/{id}/seats` | List seats (`?status=AVAILABLE`) |

### Bookings — `/api/bookings`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/bookings` | **Book seat** (row lock) — body: `{ "seat_id", "user_id" }` |
| GET | `/api/bookings/{id}` | Get booking |
| DELETE | `/api/bookings/{id}` | Cancel booking |
| GET | `/api/bookings/event/{id}/available` | Available seats |
| GET | `/api/bookings/event/{id}/booked` | Booked seats |
| GET | `/api/bookings/event/{id}/stats` | Statistics |

### Demo — `/api/demo`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/demo/seed` | Load sample data |
| GET | `/api/demo/status` | DB counts |

### UI routes

| Route | Page |
|-------|------|
| `/` | Home |
| `/events` | Events |
| `/events/{id}` | Seat map + booking |
| `/booking/success` | Ticket |
| `/cancel` | Cancel booking |
| `/stats` | Statistics |
| `/concurrency-demo` | How it works |

---

## Installation

### Prerequisites

- Python **3.9+**
- PostgreSQL **14+**

### 1. Clone

```bash
git clone <your-repo-url>
cd Flask-ticket-booking
```

### 2. Virtual environment

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. PostgreSQL setup

```bash
psql -U postgres -f scripts/create_database.sql
```

Or create manually:

```sql
CREATE USER booking_user WITH PASSWORD 'booking_pass';
CREATE DATABASE booking_db OWNER booking_user;
```

### 4. Configure `.env`

```bash
copy .env.example .env
```

```env
DATABASE_URL=postgresql+psycopg2://booking_user:booking_pass@localhost:5432/booking_db
APP_ENV=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

### 5. Seed data

```bash
python seed_data.py --reset
```

### 6. Run

```bash
python run.py
```

Or:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| URL | Purpose |
|-----|---------|
| http://localhost:8000 | Web UI |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/health | Health |

---

## Testing

### Unit & concurrency tests

```bash
pytest tests/ -v
```

- `tests/test_booking.py` — book, conflict, API, cancel/rebook
- `tests/test_concurrency.py` — 50/51 concurrent bookings, concurrent cancel

Tests use in-memory SQLite with `StaticPool` (production concurrency is validated on **PostgreSQL**).

### HTTP load test

```bash
# Terminal 1
python run.py

# Terminal 2
python tests/simulate_load.py
```

Expected: **1× 201**, **50× 409** for 51 concurrent requests on one seat.

---

## Project structure

```
Flask-ticket-booking/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory
│   ├── database.py          # SQLAlchemy engine + get_db
│   ├── config.py
│   ├── templating.py        # Jinja2 + INR filter
│   ├── demo_seed.py
│   ├── schema_utils.py
│   ├── models/
│   │   ├── event.py
│   │   ├── seat.py
│   │   └── booking.py
│   ├── routes/
│   │   ├── events.py
│   │   ├── bookings.py
│   │   ├── pages.py
│   │   └── demo.py
│   └── services/
│       └── booking_mgr.py
├── templates/
├── static/
│   ├── css/style.css
│   └── js/app.js
├── tests/
│   ├── conftest.py
│   ├── test_booking.py
│   ├── test_concurrency.py
│   └── simulate_load.py
├── scripts/
│   ├── create_database.sql
│   └── add_event_columns.sql
├── screenshots/
├── run.py                   # Uvicorn entry
├── seed_data.py
├── requirements.txt
├── pytest.ini
├── .env.example
├── GETTING_STARTED.md
└── README.md
```

---

## Portfolio copy

### Resume project line

**Concurrency-Safe Ticketing System | Python, FastAPI, PostgreSQL, Threading**

- Developed a concurrency-safe ticket booking API using **PostgreSQL row-level locking** (`SELECT ... FOR UPDATE`) to prevent double-booking.
- Handled **50+ concurrent booking requests** while ensuring data consistency and transactional integrity.

### LinkedIn project description

Built **TicketFlow**, a full-stack ticket booking platform with **FastAPI**, **PostgreSQL**, and a responsive web UI. Implemented row-level locking and unique constraints so only one of 50+ simultaneous booking attempts can claim a seat. Includes cinema-style seat selection, live statistics, cancellation flow, pytest concurrency tests, and an HTTP load-test script.

### GitHub repository description

Concurrency-safe ticket booking API and UI — FastAPI, PostgreSQL, SQLAlchemy, row-level locking. Cinema seat maps, live stats, 50+ concurrent request tests.

---

## Quick reference

| Task | Command |
|------|---------|
| Run server | `python run.py` or `uvicorn app.main:app --reload` |
| Seed data | `python seed_data.py --reset` |
| Tests | `pytest tests/ -v` |
| Load test | `python tests/simulate_load.py` |
| API docs | http://localhost:8000/docs |

---

## Further reading

- [`GETTING_STARTED.md`](GETTING_STARTED.md) — condensed setup
- Concurrency demo: http://localhost:8000/concurrency-demo
