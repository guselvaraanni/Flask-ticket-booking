-- PostgreSQL setup for TicketFlow
-- Run as a superuser, e.g. psql -U postgres -f scripts/create_database.sql

CREATE USER booking_user WITH PASSWORD 'booking_pass';

CREATE DATABASE booking_db
  OWNER booking_user
  ENCODING 'UTF8'
  LC_COLLATE 'en_US.UTF-8'
  LC_CTYPE 'en_US.UTF-8'
  TEMPLATE template0;

GRANT ALL PRIVILEGES ON DATABASE booking_db TO booking_user;

-- Connect to booking_db and grant schema privileges:
-- \c booking_db
-- GRANT ALL ON SCHEMA public TO booking_user;
