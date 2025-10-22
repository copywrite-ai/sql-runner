
-- Migration file: Adding new columns and indexes
-- This demonstrates idempotent column additions

ALTER TABLE users ADD COLUMN phone VARCHAR(20);
ALTER TABLE users ADD COLUMN address TEXT;
ALTER TABLE users ADD COLUMN birth_date DATE;

-- Add indexes for new columns
CREATE INDEX idx_phone ON users (phone);
CREATE INDEX idx_birth_date ON users (birth_date);
