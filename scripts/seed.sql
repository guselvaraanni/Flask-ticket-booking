-- Optional SQL reference for demo data (app uses seed_data.py for full setup).
-- Run after tables exist: mysql -u root -p booking_db < scripts/seed.sql

-- Note: seat generation is row-based (A1..J10 etc.) — use python seed_data.py instead.

CREATE DATABASE IF NOT EXISTS booking_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE booking_db;

-- Verify
SHOW TABLES;
