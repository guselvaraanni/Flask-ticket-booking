-- Run once on existing MySQL databases after UI upgrade.
USE booking_db;

ALTER TABLE events ADD COLUMN description TEXT NULL;
ALTER TABLE events ADD COLUMN ticket_price FLOAT DEFAULT 25.0;
ALTER TABLE events ADD COLUMN category VARCHAR(50) DEFAULT 'general';

-- If a column already exists, skip that line or ignore the duplicate-column error.
