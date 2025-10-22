
-- Sample data insertion
-- DML statements don't need idempotent checks

INSERT INTO users (username, email, age, status) VALUES
('john_doe', 'john@example.com', 25, 'active'),
('jane_smith', 'jane@example.com', 30, 'active'),
('bob_wilson', 'bob@example.com', 35, 'inactive');

-- Update existing data
UPDATE users SET status = 'premium' WHERE age > 28;
