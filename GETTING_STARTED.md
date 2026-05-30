# Getting Started Guide

## Step 1: Prerequisites

Make sure you have installed:

* Python 3.8+: https://www.python.org/downloads/
* MySQL 8.0+: https://dev.mysql.com/downloads/mysql/
* Git: https://git-scm.com/

Verify installations:

```bash
python --version
mysql --version
git --version
```

## Step 2: Clone the Project

```bash
git clone https://github.com/yourusername/flask-booking-api.git
cd flask-booking-api
```

## Step 3: Install Python Dependencies

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

## Step 4: Create the MySQL Database

Log in to MySQL:

```bash
mysql -u root -p
```

Run:

```sql
CREATE DATABASE IF NOT EXISTS booking_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

SHOW DATABASES LIKE 'booking_db';
```

Or use the project script:

```bash
mysql -u root -p < scripts/create_database.sql
```

## Step 5: Configure Environment Variables

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Edit `.env` and replace `MY_PASSWORD` with your MySQL root password:

```env
DATABASE_URL=mysql+pymysql://root:MY_PASSWORD@localhost:3306/booking_db?charset=utf8mb4
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=True
```

## Step 6: Start the Application

```bash
python run.py
```

You should see:

```
* Running on http://0.0.0.0:5000
```

Tables are created automatically on first startup.

## Step 7: Test the API

### Option A: Swagger UI (Recommended)

Open: http://localhost:5000/apidocs

### Option B: curl

```bash
curl http://localhost:5000/health

curl -X POST http://localhost:5000/api/events \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Concert 2024\", \"date\": \"2024-06-15T19:00:00\", \"location\": \"Madison Square Garden\"}"

curl -X POST http://localhost:5000/api/events/1/seats \
  -H "Content-Type: application/json" \
  -d "{\"num_rows\": 5, \"seats_per_row\": 20}"

curl -X POST http://localhost:5000/api/bookings \
  -H "Content-Type: application/json" \
  -d "{\"seat_id\": 1, \"user_id\": \"user@example.com\"}"
```

## Step 8: Run the Load Test

In a second terminal (with the API still running):

```bash
python tests/simulate_load.py
```

**Expected output:**

* 1 booking succeeds (201 Created)
* 50 conflicts (409 Conflict) with 51 concurrent requests
* `TEST PASSED` and exit code 0
* Database shows exactly 1 booked seat

## Step 9: Verify Tables in MySQL (Optional)

```bash
mysql -u root -p booking_db
```

```sql
SHOW TABLES;
DESCRIBE events;
DESCRIBE seats;
DESCRIBE bookings;
SELECT * FROM seats WHERE id = 1;
SELECT COUNT(*) FROM bookings;
```

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'pymysql'`

**Solution:** `pip install -r requirements.txt`

### Issue: `Can't connect to MySQL server`

**Solution:** Start MySQL service and confirm host/port/user/password in `.env`.

### Issue: `Unknown database 'booking_db'`

**Solution:** Run `scripts/create_database.sql` or the `CREATE DATABASE` command above.

### Issue: `.env` not loaded / wrong database URL

**Solution:** Ensure `.env` is in the project root. `run.py` and `app/config.py` call `load_dotenv()`.

### Issue: Load test times out

**Solution:** Confirm `python run.py` is running. Increase `TIMEOUT` in `tests/simulate_load.py` if needed.

## Key Files to Study

### Row-Level Locking

**File:** `app/services/booking_mgr.py`

```python
seat = Seat.query.with_for_update().filter_by(id=seat_id).first()
```

MySQL InnoDB holds this lock until the transaction commits.

### Booking Route

**File:** `app/routes/bookings.py`

* 201: Booking successful
* 409: Seat already booked
* 404: Seat not found

### Load Test

**File:** `tests/simulate_load.py`

Uses `ThreadPoolExecutor` to fire 51 concurrent requests at the same seat.

## Interview Preparation

1. **Problem:** Two users book the same seat at the same time.
2. **Solution:** MySQL InnoDB `SELECT ... FOR UPDATE` via SQLAlchemy `.with_for_update()`.
3. **Flow:** First transaction locks the row; others wait; winner commits; losers see `BOOKED` and get 409.
4. **Proof:** Load test with 51 concurrent requests — exactly one success, consistent DB state.

---

**Happy coding!**
