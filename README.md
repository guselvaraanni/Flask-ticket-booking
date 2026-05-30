# TicketFlow — Concurrency-Safe Ticket Booking Platform

A full-stack seat booking application with a **production-style web UI** and a **concurrency-safe REST API**. Multiple users can attempt to book the same seat at the same time; MySQL InnoDB row-level locking ensures exactly one booking succeeds.

![TicketFlow Home](screenshots/Screenshot%202026-05-30%20132932.png)

---

## Project Overview

### What problem does this solve?

In high-traffic ticketing (concerts, movies, conferences), many users often click **Book** on the same seat within milliseconds. Without proper synchronization, two requests can both see the seat as available and both commit—causing **double bookings** and inconsistent inventory.

**TicketFlow** solves this with:

- **Database-level row locks** (`SELECT ... FOR UPDATE`) before checking or updating seat status  
- **ACID transactions** on MySQL InnoDB  
- A **unique constraint** on `bookings.seat_id` as a safety net  
- Automated **concurrency and load tests** to prove correctness  

### Why concurrency-safe booking matters

Race conditions are not visible in single-user demos but appear immediately under real load. This project is designed to demonstrate **correct behavior under contention**—the same guarantees expected from platforms like BookMyShow or Ticketmaster at the data layer.

### Technology stack

| Layer | Technologies |
|--------|----------------|
| **Frontend** | HTML5, Jinja2 templates, vanilla CSS (`static/css/style.css`), vanilla JavaScript (`static/js/app.js`) |
| **Backend** | Python 3.8+, Flask 3, Flask-SQLAlchemy, Flask-Migrate |
| **Database** | MySQL 8+ (InnoDB), PyMySQL driver |
| **API docs** | Flasgger (Swagger UI at `/apidocs`) |
| **Testing** | pytest, `ThreadPoolExecutor` load script |

---

## Features

| Feature | Description |
|---------|-------------|
| **Event management** | Create/list events via API; browse events in the UI with category banners (Movie, Concert, Conference). |
| **Movie-style seat selection** | Interactive cinema grid (rows A–H, numbered seats), color-coded Available / Booked / Selected / Unavailable. |
| **Real-time availability** | Seat map and headers load live data from `/api/events/<id>/seats` and `/api/bookings/event/<id>/stats`. |
| **Booking confirmation** | Digital ticket with Booking ID, transaction UUID, seat number, and print/download actions. |
| **Cancellation** | Search by Booking ID, review details, confirm in a modal; seat returns to `AVAILABLE`. |
| **Statistics dashboard** | Global and per-event occupancy, bar charts, and occupancy progress. |
| **Demo data loader** | `python seed_data.py` or `POST /api/demo/seed` — three sample events (450 seats total). |
| **Concurrency protection** | `BookingManager.book_seat()` / `cancel_booking()` use `with_for_update()` row locks. |
| **MySQL integration** | `mysql+pymysql://` connection string, connection pooling, InnoDB tables. |
| **Responsive UI** | Mobile-first CSS (320px–1920px), hamburger navigation, contained seat-map scroll on phones. |

---

## User journey

```
Home → Events → Select event → Pick seat → Enter email → Book
  → Ticket confirmation → (optional) Cancel booking
Statistics and “How it works” available from the navbar at any time.
```

---

## Application screenshots

Screenshots are in [`screenshots/`](screenshots/). They are ordered by **user flow**, not filename.

### 1. Home page

Landing page with hero copy, live stats (events, seats, availability, occupancy), and featured event cards.

![Home page — hero and live statistics](screenshots/Screenshot%202026-05-30%20132932.png)

*Portfolio positioning, aggregate metrics, and entry points to browse events or learn how concurrency is enforced.*

---

### 2. Events listing

Dedicated events page with category cards, pricing in INR, and availability counts.

![Events listing](screenshots/Screenshot%202026-05-30%20133008.png)

*Users choose Movie Night, Music Concert, or Tech Conference and proceed to seat selection via **Book Now**.*

---

### 3. Home page — featured events & trust highlights

The home page also surfaces the same events plus cards explaining row-level locking, unique constraints, and load testing.

![Home page — featured events and technical highlights](screenshots/Screenshot%202026-05-30%20132954.png)

*Reinforces the concurrency story for reviewers and interview demos.*

---

### 4. Event details (booking page header)

Each event has a detail route: `/events/<id>`. The header shows category, venue, date/time, description, and live Available / Booked / price stats.

*Event metadata appears at the top of the integrated booking page (see next screenshot).*

---

### 5. Seat selection

Cinema-style seat map with SCREEN indicator, legend, and a sticky **Your Ticket** panel.

![Seat selection — Music Concert](screenshots/Screenshot%202026-05-30%20133054.png)

*Green = available, red = booked, blue = selected. Users tap a seat to open the inline booking form.*

---

### 6. Booking flow

After selecting a seat, users enter an email/User ID and click **Book Ticket**. The UI calls `POST /api/bookings` and redirects to the ticket page on success.

*The booking form is on the same page as the seat map (right panel in the screenshot above).*

---

### 7. Booking success

Confirmed ticket with CONFIRMED badge, seat block, transaction ID, and barcode-style footer.

![Booking success — digital ticket](screenshots/Screenshot%202026-05-30%20133107.png)

*Actions: Download Ticket, Print Ticket, Book Another, Cancel Booking.*

#### Print preview

![Print ticket preview](screenshots/Screenshot%202026-05-30%20133123.png)

*Browser print layout for a clean paper/PDF ticket.*

---

### 8. Statistics dashboard

Live occupancy across all events, with per-event filter and seat distribution bars.

![Statistics dashboard](screenshots/Screenshot%202026-05-30%20133144.png)

*Overview cards plus event-specific totals and visual breakdown (available vs booked).*

---

### 9. Cancellation page

#### Search and booking details

![Cancel booking — search and details](screenshots/Screenshot%202026-05-30%20133203.png)

*Enter Booking ID, view event/seat/transaction/guest details, and start cancellation.*

#### Confirmation modal

![Cancel booking — confirmation modal](screenshots/Screenshot%202026-05-30%20133215.png)

*Destructive action requires explicit confirmation before `DELETE /api/bookings/<id>`.*

#### Success state

![Cancel booking — success](screenshots/Screenshot%202026-05-30%20133226.png)

*Seat is released back to inventory; toast confirms cancellation.*

---

### 10. How it works (concurrency demo)

Educational page at `/concurrency-demo` explaining locking, constraints, and the dual-request flow.

![Concurrency demo — overview](screenshots/Screenshot%202026-05-30%20133306.png)

![Concurrency demo — booking flow diagram](screenshots/Screenshot%202026-05-30%20133322.png)

*Includes steps to reproduce 409 conflicts and run `tests/simulate_load.py` / pytest.*

---

### 11. Mobile & responsive layouts

No separate mobile-only screenshots are in the repo. The UI is responsive across **320px–1920px** (hamburger nav ≤768px, stacked cards, contained horizontal scroll for wide seat rows on small screens). Test with browser DevTools device mode or a real phone on the same URLs.

---

## Architecture

### Frontend

| Component | Role |
|-----------|------|
| **Jinja2 templates** | Server-rendered pages (`templates/`) extending `base.html` |
| **CSS** | Single design system in `static/css/style.css` — CSS Grid, Flexbox, `clamp()`, responsive breakpoints |
| **JavaScript** | `static/js/app.js` — API calls, seat map rendering, stats, cancel flow, demo seed, health check |

The UI **does not** bypass the API: all writes go to existing `/api/*` endpoints.

### Backend

| Component | Role |
|-----------|------|
| **Flask** | App factory in `app/__init__.py`, blueprints for API + UI |
| **SQLAlchemy** | ORM models, sessions, `with_for_update()` |
| **MySQL** | Primary datastore (InnoDB required for row locks and FKs) |
| **Service layer** | `app/services/booking_mgr.py` — booking/cancel business logic |
| **Routes** | `app/routes/events.py`, `bookings.py`, `pages.py`, `demo.py` |

### Database schema

#### `events`

| Column | Purpose |
|--------|---------|
| `id` | Primary key |
| `name`, `date`, `location` | Event metadata |
| `description`, `ticket_price`, `category` | UI presentation |
| `total_seats` | Cached seat count |

#### `seats`

| Column | Purpose |
|--------|---------|
| `id` | Primary key |
| `event_id` | FK → `events.id` |
| `seat_number`, `row_letter` | e.g. `A1`, row `A` |
| `status` | `AVAILABLE` or `BOOKED` |
| **Constraints** | `UNIQUE (event_id, seat_number)`; index on `(event_id, status)` |

#### `bookings`

| Column | Purpose |
|--------|---------|
| `id` | Primary key |
| `seat_id` | FK → `seats.id`, **UNIQUE** (one booking per seat) |
| `user_id` | Guest identifier (email string) |
| `transaction_id` | UUID for ticket display |
| `booking_timestamp` | When the booking was created |

Tables are created via `db.create_all()` on startup. Existing databases get presentation columns through `app/schema_utils.py`.

### Concurrency layer

```
Client A ──POST /api/bookings──┐
                               ├──► BEGIN TRANSACTION
Client B ──POST /api/bookings──┘         │
                                         ▼
                              SELECT ... FOR UPDATE (seat row)
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
              First locker                               Second waits
              status = AVAILABLE                         then sees BOOKED
              INSERT booking                             → 409 Conflict
              COMMIT
              → 201 Created
```

| Mechanism | Implementation |
|-----------|----------------|
| **Row-level locking** | `Seat.query.with_for_update().filter_by(id=seat_id)` in `book_seat()` |
| **Cancel safety** | `Booking` and `Seat` rows locked with `with_for_update()` in `cancel_booking()` |
| **Unique constraint** | `bookings.seat_id` UNIQUE — duplicate insert fails even if app logic regresses |
| **Transactions** | `db.session.commit()` / `rollback()` on success or `IntegrityError` |

---

## API documentation summary

Interactive Swagger UI: **`http://localhost:5000/apidocs`** after starting the server.

### System

| Method | Endpoint | Purpose | Request | Response |
|--------|----------|---------|---------|----------|
| GET | `/health` | Liveness check | — | `200` `{ "status": "healthy", ... }` |
| GET | `/api` | API metadata | — | `200` links to docs and UI |

### Events (`/api/events`)

| Method | Endpoint | Purpose | Request body | Response |
|--------|----------|---------|----------------|----------|
| POST | `/api/events` | Create event | `{ "name", "date", "location"? }` | `201` event object |
| GET | `/api/events` | List events | — | `200` array of events |
| GET | `/api/events/<id>` | Get event | — | `200` event / `404` |
| POST | `/api/events/<id>/seats` | Bulk create seats | `{ "num_rows", "seats_per_row" }` | `201` summary |
| GET | `/api/events/<id>/seats` | List seats | Query: `?status=AVAILABLE` | `200` array of seats |

### Bookings (`/api/bookings`)

| Method | Endpoint | Purpose | Request body | Response |
|--------|----------|---------|----------------|----------|
| POST | `/api/bookings` | **Book seat** (locked) | `{ "seat_id", "user_id" }` | `201` booking / `409` conflict / `404` |
| GET | `/api/bookings/<id>` | Get booking | — | `200` booking / `404` |
| DELETE | `/api/bookings/<id>` | Cancel booking | — | `200` message / `404` |
| GET | `/api/bookings/event/<id>/available` | Available seats | — | `200` `{ available_seats, count }` |
| GET | `/api/bookings/event/<id>/booked` | Booked seats | — | `200` `{ booked_seats, count }` |
| GET | `/api/bookings/event/<id>/stats` | Event statistics | — | `200` `{ stats: { total_seats, booked_seats, available_seats, occupancy_rate } }` |

### Demo (`/api/demo`)

| Method | Endpoint | Purpose | Request body | Response |
|--------|----------|---------|----------------|----------|
| POST | `/api/demo/seed` | Load sample data | `{ "reset"?, "include_bookings"? }` | `200` seed summary |
| GET | `/api/demo/status` | Counts / ready flag | — | `200` `{ events, seats, bookings, ready }` |

### UI helper

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| GET | `/api/ui/booking/<id>` | Booking details for cancel page | `200` booking + event + seat info / `404` |

### UI routes (HTML)

| Route | Page |
|-------|------|
| `/` | Home |
| `/events` | Events listing |
| `/events/<id>` | Seat selection & booking |
| `/booking/success` | Ticket confirmation |
| `/cancel` | Cancel booking |
| `/stats`, `/stats/<id>` | Statistics |
| `/concurrency-demo` | How it works |

---

## Installation guide

### Prerequisites

- Python **3.8+**
- MySQL **8.0+** (InnoDB)
- Git

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd Flask-ticket-booking
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux
```

Edit `.env`:

```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/booking_db?charset=utf8mb4
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=True
```

### 5. Create the MySQL database

```sql
CREATE DATABASE IF NOT EXISTS booking_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Or use the provided script:

```bash
mysql -u root -p < scripts/create_database.sql
```

### 6. Seed demo data (recommended)

```bash
python seed_data.py
# Or reset and reseed:
python seed_data.py --reset
```

This creates **Movie Night** (100 seats), **Music Concert** (150), and **Tech Conference** (200) with sample bookings.

### 7. Run the application

```bash
python run.py
```

Open:

- **Web UI:** http://localhost:5000  
- **Swagger:** http://localhost:5000/apidocs  
- **Health:** http://localhost:5000/health  

---

## Testing

### Unit tests (pytest)

Uses in-memory SQLite for speed (`tests/conftest.py`). Covers booking success, conflict, API integration, and cancel behavior.

```bash
pytest tests/ -v
```

Key files:

- `tests/test_booking.py` — single-user book/conflict/API/cancel  
- `tests/test_concurrency.py` — 50 concurrent books (1 success), concurrent cancel, book-after-cancel  

### Concurrency tests

```bash
pytest tests/test_concurrency.py -v
```

Validates that under `ThreadPoolExecutor` load, exactly **one** booking succeeds and **49** receive `409` for the same seat.

### Load tests (HTTP client)

Simulates **51** concurrent `POST /api/bookings` requests against a running server:

```bash
# Terminal 1
python run.py

# Terminal 2
python tests/simulate_load.py
```

**Expected:** 1× `201 Created`, 50× `409 Conflict`, zero errors, exactly one row in `bookings` for the target seat.

---

## Project structure

Exact layout of the repository (excluding `.git`, `__pycache__`, `.pytest_cache`, and local `venv`):

```
Flask-ticket-booking/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── demo_seed.py
│   ├── extensions.py
│   ├── schema_utils.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── booking.py
│   │   ├── event.py
│   │   └── seat.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── bookings.py
│   │   ├── demo.py
│   │   ├── events.py
│   │   └── pages.py
│   └── services/
│       ├── __init__.py
│       └── booking_mgr.py
├── screenshots/
│   ├── Screenshot 2026-05-30 132932.png
│   ├── Screenshot 2026-05-30 132954.png
│   ├── Screenshot 2026-05-30 133008.png
│   ├── Screenshot 2026-05-30 133054.png
│   ├── Screenshot 2026-05-30 133107.png
│   ├── Screenshot 2026-05-30 133123.png
│   ├── Screenshot 2026-05-30 133144.png
│   ├── Screenshot 2026-05-30 133203.png
│   ├── Screenshot 2026-05-30 133215.png
│   ├── Screenshot 2026-05-30 133226.png
│   ├── Screenshot 2026-05-30 133306.png
│   └── Screenshot 2026-05-30 133322.png
├── scripts/
│   ├── add_event_columns.sql
│   ├── create_database.sql
│   └── seed.sql
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/
│   ├── partials/
│   │   └── event_card.html
│   ├── base.html
│   ├── book.html
│   ├── booking_success.html
│   ├── cancel.html
│   ├── concurrency_demo.html
│   ├── event_detail.html
│   ├── events.html
│   ├── index.html
│   └── stats.html
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── simulate_load.py
│   ├── test_booking.py
│   └── test_concurrency.py
├── .env.example
├── .gitignore
├── GETTING_STARTED.md
├── README.md
├── requirements.txt
├── run.py
└── seed_data.py
```

---

## Quick reference

| Task | Command |
|------|---------|
| Start server | `python run.py` |
| Seed demo data | `python seed_data.py --reset` |
| Run unit tests | `pytest tests/ -v` |
| Load test | `python tests/simulate_load.py` |
| API docs | http://localhost:5000/apidocs |

---

## License

See repository license file if present. For portfolio and educational use.

---

## Further reading

- [`GETTING_STARTED.md`](GETTING_STARTED.md) — condensed setup notes  
- **Concurrency demo:** http://localhost:5000/concurrency-demo  
