#!/usr/bin/env python3
"""
Demo script showing how to use MySQLSchemaManager
This is a demonstration of the API without requiring an actual database connection
"""

from mysql_schema_manager import MySQLSchemaManager


def demo_api_usage():
    """Demonstrate the API usage patterns"""

    print("=== MySQL Schema Manager API Demo ===\n")

    # 1. Initialize the manager
    config = {
        'host': 'localhost',
        'username': 'your_username',
        'password': 'your_password',
        'database': 'your_database',
        'port': 3306
    }

    print("1. Initialize the schema manager:")
    print(f"   manager = MySQLSchemaManager({config})")
    print()

    # Create instance (this won't connect to database)
    manager = MySQLSchemaManager(**config)
    print("✓ Schema manager initialized successfully\n")

    # 2. Show available methods
    print("2. Available methods:")
    methods = [
        ('connect()', 'Establish database connection'),
        ('disconnect()', 'Close database connection'),
        ('table_exists(table_name)', 'Check if table exists'),
        ('column_exists(table_name, column_name)', 'Check if column exists'),
        ('index_exists(table_name, index_name)', 'Check if index exists'),
        ('create_table_with_drop(table_name, create_sql)', 'Create table with drop if exists'),
        ('alter_table_add_column(table_name, column_name, definition)', 'Add column with existence check'),
        ('create_index_with_check(table_name, index_name, columns)', 'Create index with existence check')
    ]

    for method, description in methods:
        print(f"   • {method:<50} - {description}")
    print()

    # 3. Example usage patterns
    print("3. Example usage patterns:")
    print()

    print("   # Connect to database")
    print("   if manager.connect():")
    print("       print('Connected successfully')")
    print()

    print("   # Create table (drops if exists)")
    print("   create_sql = '''")
    print("   CREATE TABLE users (")
    print("       id INT AUTO_INCREMENT PRIMARY KEY,")
    print("       username VARCHAR(50) NOT NULL,")
    print("       email VARCHAR(100) NOT NULL")
    print("   ) ENGINE=InnoDB")
    print("   '''")
    print("   manager.create_table_with_drop('users', create_sql)")
    print()

    print("   # Add column (checks existence and definition)")
    print("   manager.alter_table_add_column('users', 'age', 'INT DEFAULT 0')")
    print("   manager.alter_table_add_column('users', 'status', \"VARCHAR(20) DEFAULT 'active'\")")
    print()

    print("   # Create indexes (drops if exists)")
    print("   manager.create_index_with_check('users', 'idx_email', ['email'])")
    print("   manager.create_index_with_check('users', 'idx_name_email', ['username', 'email'])")
    print("   manager.create_index_with_check('users', 'idx_age', ['age'], unique=False)")
    print()

    print("   # Always disconnect when done")
    print("   manager.disconnect()")
    print()

    # 4. Safety features
    print("4. Safety features:")
    print("   ✓ All existence checks use information_schema")
    print("   ✓ Parameterized queries prevent SQL injection")
    print("   ✓ Column definitions are compared before modification")
    print("   ✓ Transactions are used with rollback on error")
    print("   ✓ Comprehensive logging of all operations")
    print()

    # 5. Advanced features
    print("5. Advanced features:")
    print("   ✓ Handles complex column definitions (NOT NULL, DEFAULT, UNIQUE, AUTO_INCREMENT)")
    print("   ✓ Supports all index types (INDEX, UNIQUE, FULLTEXT, SPATIAL)")
    print("   ✓ Normalizes column definition comparison")
    print("   ✓ Detailed error reporting with logging")
    print()


def demo_sql_examples():
    """Show examples of SQL that would be generated"""

    print("=== Generated SQL Examples ===\n")

    print("1. CREATE TABLE with DROP IF EXISTS:")
    print("   DROP TABLE IF EXISTS users;")
    print("   CREATE TABLE users (")
    print("       id INT AUTO_INCREMENT PRIMARY KEY,")
    print("       username VARCHAR(50) NOT NULL UNIQUE,")
    print("       email VARCHAR(100) NOT NULL,")
    print("       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    print("   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;")
    print()

    print("2. ALTER TABLE ADD COLUMN:")
    print("   -- Column doesn't exist:")
    print("   ALTER TABLE users ADD COLUMN age INT DEFAULT 0;")
    print()
    print("   -- Column exists with different definition:")
    print("   ALTER TABLE users DROP COLUMN age;")
    print("   ALTER TABLE users ADD COLUMN age VARCHAR(10) DEFAULT 'unknown';")
    print()
    print("   -- Column exists with same definition: (no SQL executed)")
    print("   -- Skipping column 'age' - already exists with same definition")
    print()

    print("3. CREATE INDEX with DROP IF EXISTS:")
    print("   -- Index exists:")
    print("   DROP INDEX idx_email ON users;")
    print("   CREATE INDEX idx_email ON users (email);")
    print()
    print("   -- Unique index:")
    print("   CREATE UNIQUE INDEX idx_username ON users (username);")
    print()
    print("   -- Composite index:")
    print("   CREATE INDEX idx_username_email ON users (username, email);")
    print()

    print("4. Information Schema Queries (used internally):")
    print("   -- Check table existence:")
    print("   SELECT COUNT(*) FROM information_schema.tables")
    print("   WHERE table_schema = 'your_database' AND table_name = 'users';")
    print()
    print("   -- Check column existence:")
    print("   SELECT COUNT(*) FROM information_schema.columns")
    print("   WHERE table_schema = 'your_database' AND table_name = 'users' AND column_name = 'email';")
    print()
    print("   -- Get column definition:")
    print("   SELECT COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, EXTRA")
    print("   FROM information_schema.columns")
    print("   WHERE table_schema = 'your_database' AND table_name = 'users' AND column_name = 'email';")
    print()


if __name__ == "__main__":
    demo_api_usage()
    demo_sql_examples()

    print("=== To run with actual database ===")
    print("1. Install MySQL connector: pip install -r requirements.txt")
    print("2. Update database connection parameters in the script")
    print("3. Run: python mysql_schema_manager.py")
    print()
    print("The script includes a complete example in the main() function!")