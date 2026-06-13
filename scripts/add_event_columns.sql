-- Run once on existing PostgreSQL databases after UI upgrade.
ALTER TABLE events ADD COLUMN IF NOT EXISTS description TEXT NULL;
ALTER TABLE events ADD COLUMN IF NOT EXISTS ticket_price DOUBLE PRECISION DEFAULT 25.0;
ALTER TABLE events ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'general';
