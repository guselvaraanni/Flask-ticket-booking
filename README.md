# High-Concurrency Seat Booking API

A Flask-based REST API for managing seat bookings in high-concurrency environments such as concerts, movie theaters, and live events. The system is designed to prevent race conditions and ensure data consistency using database-level locking.

---

## Overview

This project focuses on a common real-world problem: multiple users attempting to book the same seat at the same time. Without proper handling, this leads to inconsistent data and duplicate bookings.

The API addresses this problem by implementing row-level locking at the database level using PostgreSQL. This ensures that only one request can successfully book a seat, even under heavy concurrent load.

---

## Problem Statement

In a concurrent system, the following sequence can occur:

* Two users check availability of the same seat at the same time
* Both requests see the seat as available
* Both proceed to book the seat
* The system ends up with duplicate bookings

This is known as a race condition.

---

## Solution Approach

The system uses PostgreSQL’s row-level locking mechanism through `SELECT ... FOR UPDATE`, implemented in SQLAlchemy via `.with_for_update()`.

When a booking request is made:

1. The seat row is locked for update
2. Other concurrent requests attempting to access the same seat are blocked
3. The first request updates the seat status to "BOOKED"
4. The transaction commits and releases the lock
5. Waiting requests resume and detect that the seat is already booked

This guarantees that only one booking can succeed.

---

## Architecture

```
flask-booking-api/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   │   ├── event.py
│   │   ├── seat.py
│   │   └── booking.py
│   ├── routes/
│   │   ├── events.py
│   │   └── bookings.py
│   └── services/
│       └── booking_mgr.py
├── tests/
│   └── simulate_load.py
├── run.py
├── requirements.txt
└── README.md
```

The project follows a service-layer pattern:

* Models define database schema
* Routes handle HTTP requests and responses
* Services contain business logic and database operations

---

## Key Design Decisions

* PostgreSQL is used for its strong support for transactions and locking
* Row-level locking ensures strict consistency during booking
* Service-layer separation improves maintainability and testability
* Unique constraints at the database level add an extra layer of safety

---

## Running the Project

### Local Setup (without Docker)

Create a virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Set environment variables:

```bash
set DATABASE_URL=postgresql://booking_user:booking_password@localhost:5432/booking_db
set FLASK_APP=run.py
set FLASK_ENV=development
```

Ensure PostgreSQL is running locally, then start the application:

```bash
python run.py
```

---

## API Summary

### Events

* Create an event
* Generate seats for an event
* Retrieve event details and seat information

### Bookings

* Book a seat (core functionality)
* Cancel a booking
* Retrieve booking details
* View available and booked seats
* Get booking statistics

---

## Booking Flow

The booking operation is implemented in `booking_mgr.py`:

```python
seat = Seat.query.with_for_update().filter_by(id=seat_id).first()

if seat.status == 'BOOKED':
    return error

seat.status = 'BOOKED'
db.session.commit()
```

This ensures:

* The seat is locked before checking availability
* No other transaction can modify the same seat concurrently
* The update is atomic

---

## Concurrency Testing

The project includes a load test that simulates multiple concurrent booking requests.

```bash
python tests/simulate_load.py
```

Expected outcome:

* Only one request succeeds
* All other requests receive a conflict response
* No duplicate bookings occur

This validates the correctness of the locking strategy.

---

## Database Schema

### Events

Stores event metadata such as name, date, and location.

### Seats

Stores individual seat information with status tracking.

### Bookings

Stores confirmed bookings and enforces a one-to-one relationship with seats.

Key constraint:

* Each seat can only be booked once

---

## Performance Considerations

* Connection pooling is enabled for efficient database usage
* Indexed queries improve lookup performance
* Lock duration is kept minimal to reduce contention
* The system can scale horizontally with multiple application instances

---

## Learning Outcomes

This project demonstrates:

* Handling race conditions in distributed systems
* Using database transactions effectively
* Designing scalable backend systems
* Structuring Flask applications for maintainability
* Writing and validating concurrency tests

---

## Future Improvements

* Add authentication and authorization
* Introduce caching for read-heavy endpoints
* Implement rate limiting
* Add background job processing
* Improve monitoring and logging

---

