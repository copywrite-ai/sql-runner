#!/usr/bin/env python3
"""
Demo script showing how to use MySQLSchemaManager to execute SQL files safely
"""

from mysql_schema_manager import MySQLSchemaManager
import os


def create_sample_sql_files():
    """Create sample SQL files for demonstration"""

    # Create a sample schema file
    schema_sql = """
-- Sample schema file for demonstration
-- This creates a simple users table with indexes

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    age INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Add indexes for better performance
CREATE INDEX idx_email ON users (email);
CREATE INDEX idx_age ON users (age);
CREATE INDEX idx_status ON users (status);
CREATE INDEX idx_username_email ON users (username, email);
"""

    # Create a sample migration file
    migration_sql = """
-- Migration file: Adding new columns and indexes
-- This demonstrates idempotent column additions

ALTER TABLE users ADD COLUMN phone VARCHAR(20);
ALTER TABLE users ADD COLUMN address TEXT;
ALTER TABLE users ADD COLUMN birth_date DATE;

-- Add indexes for new columns
CREATE INDEX idx_phone ON users (phone);
CREATE INDEX idx_birth_date ON users (birth_date);
"""

    # Create a sample data file
    data_sql = """
-- Sample data insertion
-- DML statements don't need idempotent checks

INSERT INTO users (username, email, age, status) VALUES
('john_doe', 'john@example.com', 25, 'active'),
('jane_smith', 'jane@example.com', 30, 'active'),
('bob_wilson', 'bob@example.com', 35, 'inactive');

-- Update existing data
UPDATE users SET status = 'premium' WHERE age > 28;
"""

    # Create a complex schema file
    complex_sql = """
-- Complex schema with multiple operations
-- This demonstrates handling of mixed SQL statements

-- Products table
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    category_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Orders table
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Order items table
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Add indexes
CREATE INDEX idx_products_category ON products (category_id);
CREATE INDEX idx_orders_user ON orders (user_id);
CREATE INDEX idx_orders_status ON orders (status);
CREATE UNIQUE INDEX idx_unique_order_product ON order_items (order_id, product_id);
"""

    # Write files
    with open('sample_schema.sql', 'w') as f:
        f.write(schema_sql)

    with open('sample_migration.sql', 'w') as f:
        f.write(migration_sql)

    with open('sample_data.sql', 'w') as f:
        f.write(data_sql)

    with open('complex_schema.sql', 'w') as f:
        f.write(complex_sql)

    print("✓ Created sample SQL files:")
    print("  - sample_schema.sql")
    print("  - sample_migration.sql")
    print("  - sample_data.sql")
    print("  - complex_schema.sql")


def demo_sql_file_execution():
    """Demonstrate SQL file execution functionality"""

    print("\n=== MySQL Schema Manager SQL File Execution Demo ===\n")

    # Database connection parameters
    config = {
        'host': 'localhost',
        'username': 'your_username',
        'password': 'your_password',
        'database': 'your_database',
        'port': 3306
    }

    print("1. Database Configuration:")
    print(f"   Host: {config['host']}")
    print(f"   Database: {config['database']}")
    print(f"   Username: {config['username']}")
    print()

    # Create manager instance
    manager = MySQLSchemaManager(**config)
    print("✓ MySQLSchemaManager initialized\n")

    # Show available methods for SQL file execution
    print("2. SQL File Execution Methods:")
    methods = [
        ('parse_sql_file(file_path)', 'Parse SQL file into individual statements'),
        ('execute_sql_file(file_path, dry_run=False)', 'Execute SQL file with idempotent safety'),
        ('execute_sql_file(file_path, dry_run=True)', 'Preview what would be executed')
    ]

    for method, description in methods:
        print(f"   • {method:<45} - {description}")
    print()

    # Demonstrate file parsing (without database connection)
    print("3. SQL File Parsing Demo:")
    sql_files = ['sample_schema.sql', 'sample_migration.sql', 'sample_data.sql', 'complex_schema.sql']

    for sql_file in sql_files:
        if os.path.exists(sql_file):
            statements = manager.parse_sql_file(sql_file)
            print(f"   📄 {sql_file}: {len(statements)} statements parsed")

            # Show first few statements
            for i, stmt in enumerate(statements[:3], 1):
                stmt_preview = stmt.replace('\n', ' ').strip()
                if len(stmt_preview) > 60:
                    stmt_preview = stmt_preview[:57] + "..."
                print(f"      {i}. {stmt_preview}")

            if len(statements) > 3:
                print(f"      ... and {len(statements) - 3} more statements")
        else:
            print(f"   ❌ {sql_file}: File not found")
        print()

    # Show usage examples
    print("4. Usage Examples:")
    print()
    print("   # Connect to database")
    print("   if manager.connect():")
    print("       print('Connected successfully')")
    print()
    print("   # Execute schema file with dry run first")
    print("   manager.execute_sql_file('sample_schema.sql', dry_run=True)")
    print()
    print("   # Actually execute the schema")
    print("   manager.execute_sql_file('sample_schema.sql')")
    print()
    print("   # Execute migration (idempotent - won't recreate existing items)")
    print("   manager.execute_sql_file('sample_migration.sql')")
    print()
    print("   # Execute data")
    print("   manager.execute_sql_file('sample_data.sql')")
    print()
    print("   # Always disconnect when done")
    print("   manager.disconnect()")
    print()

    # Show safety features
    print("5. Idempotent Safety Features:")
    print("   ✓ CREATE TABLE: Checks if table exists before creating")
    print("   ✓ ALTER TABLE ADD COLUMN: Checks column definition before adding")
    print("   ✓ CREATE INDEX: Checks if index exists before creating")
    print("   ✓ DML statements: Executed directly (no idempotent check needed)")
    print("   ✓ Comprehensive error handling and logging")
    print("   ✓ Dry run mode to preview changes")
    print()

    # Show supported SQL features
    print("6. Supported SQL Features:")
    print("   ✓ CREATE TABLE with all MySQL options")
    print("   ✓ ALTER TABLE ADD COLUMN with definition comparison")
    print("   ✓ CREATE INDEX and CREATE UNIQUE INDEX")
    print("   ✓ INSERT, UPDATE, DELETE statements")
    print("   ✓ Comment removal and statement parsing")
    print("   ✓ String literal handling in SQL")
    print("   ✓ Complex multi-table schemas")
    print()

    # Show example with actual database connection (commented out)
    print("7. Production Usage Example:")
    print("""
    # Production script
    import logging
    from mysql_schema_manager import MySQLSchemaManager

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Load config from environment or config file
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'username': os.getenv('DB_USER', 'your_username'),
        'password': os.getenv('DB_PASSWORD', 'your_password'),
        'database': os.getenv('DB_NAME', 'your_database'),
        'port': int(os.getenv('DB_PORT', '3306'))
    }

    manager = MySQLSchemaManager(**config)

    try:
        if manager.connect():
            # Execute schema files in order
            sql_files = ['schema.sql', 'migrations.sql', 'data.sql']

            for sql_file in sql_files:
                if os.path.exists(sql_file):
                    print(f"Executing {sql_file}...")
                    if manager.execute_sql_file(sql_file):
                        print(f"✓ {sql_file} executed successfully")
                    else:
                        print(f"✗ {sql_file} execution failed")
                        break
                else:
                    print(f"⚠️ {sql_file} not found, skipping")

    finally:
        manager.disconnect()
    """)


def demo_advanced_features():
    """Demonstrate advanced features of SQL file execution"""

    print("\n=== Advanced Features Demo ===\n")

    print("1. Statement Parsing Features:")
    print("   ✓ Handles quoted strings with semicolons: INSERT INTO table VALUES ('text;with;semicolons')")
    print("   ✓ Removes single-line comments (-- comment)")
    print("   ✓ Removes multi-line comments (/* comment */)")
    print("   ✓ Preserves stored procedures and triggers")
    print("   ✓ Handles complex table definitions")
    print()

    print("2. Idempotent Operations:")
    print("   CREATE TABLE:")
    print("   - Checks if table exists")
    print("   - Skips creation if already exists")
    print("   - Logs action taken")
    print()
    print("   ALTER TABLE ADD COLUMN:")
    print("   - Checks if column exists")
    print("   - Compares column definitions")
    print("   - Skips if same definition")
    print("   - Drops and recreates if different")
    print()
    print("   CREATE INDEX:")
    print("   - Checks if index exists")
    print("   - Skips creation if already exists")
    print("   - Handles unique indexes")
    print()

    print("3. Error Handling:")
    print("   ✓ Individual statement errors don't stop execution")
    print("   ✓ Detailed error logging with statement context")
    print("   ✓ Transaction rollback on failure")
    print("   ✓ Summary report with success/skip/error counts")
    print()

    print("4. Logging and Monitoring:")
    print("   ✓ Detailed logging of all operations")
    print("   ✓ Progress tracking during file execution")
    print("   ✓ Clear indication of what was executed vs skipped")
    print("   ✓ Performance monitoring opportunities")
    print()


if __name__ == "__main__":
    print("Creating sample SQL files...")
    create_sample_sql_files()

    demo_sql_file_execution()
    demo_advanced_features()

    print("=== To run with actual database ===")
    print("1. Install MySQL connector: pip install -r requirements.txt")
    print("2. Update database connection parameters")
    print("3. Run: python sql_file_demo.py")
    print("4. Modify the demo to actually connect and execute SQL files")
    print()
    print("The demo creates sample SQL files you can examine:")
    print("- sample_schema.sql: Basic schema with users table")
    print("- sample_migration.sql: Column additions showing idempotent behavior")
    print("- sample_data.sql: DML statements")
    print("- complex_schema.sql: Multi-table schema with foreign keys")