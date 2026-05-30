-- Create the booking database (run as MySQL root or a user with CREATE privilege)
CREATE DATABASE IF NOT EXISTS booking_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Verify creation
SHOW DATABASES LIKE 'booking_db';
