# Getting Started — TicketFlow

Quick setup for the **FastAPI + PostgreSQL** ticket booking application.

## Prerequisites

* Python 3.9+ (3.8 may work; 3.9+ recommended)
* PostgreSQL 14+: https://www.postgresql.org/download/

Verify:

```bash
python --version
psql --version
```

## Step 1: Clone and enter the project

```bash
git clone https://github.com/yourusername/ticketflow-booking.git
cd Flask-ticket-booking
```

## Step 2: Virtual environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

## Step 3: PostgreSQL database and user

Option A — SQL script (as superuser):

```bash
psql -U postgres -f scripts/create_database.sql
```

Option B — manual:

```sql
CREATE USER booking_user WITH PASSWORD 'booking_pass';
CREATE DATABASE booking_db OWNER booking_user ENCODING 'UTF8';
GRANT ALL PRIVILEGES ON DATABASE booking_db TO booking_user;
```

## Step 4: Environment variables

```bash
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux
```

Edit `.env`:

```env
DATABASE_URL=postgresql+psycopg2://booking_user:booking_pass@localhost:5432/booking_db
APP_ENV=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

## Step 5: Seed demo data

```bash
python seed_data.py
# Or reset:
python seed_data.py --reset
```

## Step 6: Run the application

```bash
python run.py
```

Or with Uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

| URL | Purpose |
|-----|---------|
| http://localhost:8000 | Web UI |
| http://localhost:8000/docs | Swagger (OpenAPI) |
| http://localhost:8000/health | Health check |

## Step 7: Run tests

```bash
pytest tests/ -v
```

## Step 8: Load test (optional)

Terminal 1: `python run.py`  
Terminal 2: `python tests/simulate_load.py`

Expected: **1** success (201), **50** conflicts (409) for 51 concurrent bookings on one seat.

## Concurrency model

PostgreSQL uses `SELECT ... FOR UPDATE` inside a transaction:

```python
seat = session.query(Seat).with_for_update().filter_by(id=seat_id).first()
```

The row lock is held until `commit()`, so only one booking can succeed per seat.

## Troubleshooting

### `ModuleNotFoundError: No module named 'psycopg2'`

```bash
pip install psycopg2-binary
```

### Cannot connect to PostgreSQL

* Confirm PostgreSQL service is running
* Check `DATABASE_URL` host, port, user, password, database name
* Ensure `booking_user` has privileges on `booking_db`

### Port already in use

Change `PORT` in `.env` or run: `uvicorn app.main:app --port 8001`
