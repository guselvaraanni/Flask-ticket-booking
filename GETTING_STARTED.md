# Getting Started Guide

## Step 1: Prerequisites

Make sure you have installed:
- Docker: https://docs.docker.com/get-docker/
- Docker Compose: https://docs.docker.com/compose/install/
- Git: https://git-scm.com/

Verify installations:
```bash
docker --version
docker-compose --version
git --version
```

## Step 2: Clone/Extract the Project

```bash
# If from GitHub
git clone https://github.com/yourusername/flask-booking-api.git
cd flask-booking-api

# Or extract from zip
unzip flask-booking-api.zip
cd flask-booking-api
```

## Step 3: Start the Application

```bash
# Build and start both Flask and PostgreSQL containers
docker-compose up --build

# On first run, this will:
# 1. Download Python 3.10 and PostgreSQL 15 images
# 2. Install dependencies (requirements.txt)
# 3. Create database tables via SQLAlchemy
# 4. Start Flask on port 5000
```

You should see output like:
```
web-1  | * Running on http://0.0.0.0:5000
```

## Step 4: Test the API

### Option A: Using Swagger UI (Recommended)
Open your browser and go to:
```
http://localhost:5000/apidocs
```

This shows all endpoints with interactive testing.

### Option B: Using curl

```bash
# Health check
curl http://localhost:5000/health

# Create an event
curl -X POST http://localhost:5000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Concert 2024",
    "date": "2024-06-15T19:00:00",
    "location": "Madison Square Garden"
  }'

# Create seats (replace 1 with your event ID)
curl -X POST http://localhost:5000/api/events/1/seats \
  -H "Content-Type: application/json" \
  -d '{
    "num_rows": 5,
    "seats_per_row": 20
  }'

# Book a seat (replace seat_id with an actual seat ID)
curl -X POST http://localhost:5000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "seat_id": 1,
    "user_id": "user@example.com"
  }'
```

### Option C: Using Postman

1. Download Postman: https://www.postman.com/downloads/
2. Import the collection from `docs/postman_collection.json` (if included)
3. Click "Send" on endpoints

## Step 5: Run the Load Test

This test simulates 50 concurrent booking requests to verify row-level locking:

```bash
# Make sure docker-compose is still running in another terminal

# Run the load test
python tests/simulate_load.py
```

**Expected output:**
- 1 booking succeeds (201 Created)
- 49 bookings fail with conflict (409 Conflict)
- All requests complete in ~1 second
- No double bookings!

## Step 6: Verify Concurrency Prevention

Check the database directly (optional):

```bash
# Access PostgreSQL inside Docker
docker exec -it flask-booking-api-db-1 psql -U booking_user -d booking_db

# Inside psql:
SELECT * FROM seats WHERE id = 1;  -- Check seat status
SELECT COUNT(*) FROM bookings;      -- Count total bookings
```

## Common Issues & Solutions

### Issue: "Connection refused" on port 5000
**Solution:** Wait 10-15 seconds for services to fully start, then refresh

### Issue: PostgreSQL container won't start
**Solution:** 
```bash
docker-compose down -v
docker-compose up --build
```
The `-v` flag removes volumes (old database data)

### Issue: "ModuleNotFoundError: No module named 'flask'"
**Solution:** Make sure you're running inside Docker (`docker-compose up`), not locally

### Issue: Load test times out
**Solution:** 
1. Wait for services to fully start
2. Increase timeout in `tests/simulate_load.py`: `TIMEOUT = 30`

## Project Structure Overview

```
flask-booking-api/
├── app/                         # Main application code
│   ├── models/                  # Database entities (Event, Seat, Booking)
│   ├── routes/                  # HTTP endpoints
│   ├── services/                # Business logic (row-level locking here!)
│   ├── __init__.py              # App factory
│   ├── config.py                # Configuration
│   └── extensions.py            # Database setup
├── tests/
│   └── simulate_load.py         # Concurrent booking test
├── Dockerfile                   # Container configuration
├── docker-compose.yml           # Service orchestration
├── requirements.txt             # Python dependencies
├── run.py                       # Entry point
└── README.md                    # Full documentation
```

## Key Files to Study (For Learning)

### 1. Row-Level Locking Implementation
**File:** `app/services/booking_mgr.py`

Look for this line:
```python
seat = Seat.query.with_for_update().filter_by(id=seat_id).first()
```

This is the **magic line** that prevents race conditions!

### 2. Booking Route
**File:** `app/routes/bookings.py`

Shows how to call the booking service and handle different HTTP status codes:
- 201: Booking successful
- 409: Seat already booked
- 404: Seat not found

### 3. Load Test
**File:** `tests/simulate_load.py`

Uses Python's `ThreadPoolExecutor` to fire 50 concurrent requests. Shows how to verify your concurrency handling works.

## Docker Commands Reference

```bash
# Start services
docker-compose up

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# View logs from specific service
docker-compose logs -f web

# Connect to Flask container
docker exec -it flask-booking-api-web-1 bash

# Connect to PostgreSQL
docker exec -it flask-booking-api-db-1 psql -U booking_user -d booking_db

# Rebuild containers
docker-compose up --build
```

## Development Workflow

### Making Changes to Code

1. Edit a Python file (e.g., `app/routes/events.py`)
2. Docker will automatically reload the Flask app (hot reload enabled)
3. Refresh your browser or re-run the curl command

### Adding a New Endpoint

1. Create a new route in `app/routes/`
2. Add docstring with Swagger annotation:
```python
@app.route('/api/custom', methods=['GET'])
def custom_endpoint():
    """
    Custom endpoint description.
    ---
    responses:
      200:
        description: Success
    """
    return jsonify({'status': 'ok'}), 200
```
3. Restart Flask: `docker-compose restart web`
4. Check `/apidocs` to see it auto-documented!

## Interview Preparation

Before your interview, be ready to explain:

1. **The Problem:**
   - "Race conditions occur when two users book the same seat simultaneously"

2. **The Solution:**
   - "I use PostgreSQL's `SELECT ... FOR UPDATE` to lock the row at the database level"
   - Reference: `app/services/booking_mgr.py` line with `.with_for_update()`

3. **How It Works:**
   - "User A's request locks the seat row"
   - "User B's request waits"
   - "User A books and commits, releasing the lock"
   - "User B's request finally reads the row, sees it's BOOKED, and returns 409 Conflict"

4. **Testing:**
   - "I created a load test that fires 50 concurrent requests at the same seat"
   - "Only 1 succeeds with 201 Created, 49 get 409 Conflict"
   - "This proves no double-booking can occur"

## Next Steps

1. ✅ Run the application locally with Docker
2. ✅ Create an event and some seats via Swagger UI
3. ✅ Manually book a seat and verify the seat status changes
4. ✅ Run the load test to see concurrency in action
5. ✅ Read through the code, especially `booking_mgr.py`
6. ✅ Study the README.md "How Concurrency is Handled" section
7. ✅ Modify the code: add a new field to a model, create a new endpoint
8. ✅ Deploy to Render.com (optional, but impressive!)

## Getting Help

- **API Documentation:** http://localhost:5000/apidocs
- **Full Guide:** README.md
- **Code Comments:** Check docstrings in Python files
- **Logs:** `docker-compose logs`

---

**Happy coding! 🚀**

Remember: The key to interviews is not just the code, but explaining the **design decisions** and **architectural choices**. This project demonstrates your understanding of concurrency, database transactions, and production-grade API design.
