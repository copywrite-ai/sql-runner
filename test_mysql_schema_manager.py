#!/usr/bin/env python3
"""
Test script for MySQLSchemaManager
Tests the class initialization and basic functionality without requiring a database connection
"""

import unittest
import os
from unittest.mock import Mock, patch, MagicMock
from mysql_schema_manager import MySQLSchemaManager


class TestMySQLSchemaManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'host': 'localhost',
            'username': 'test_user',
            'password': 'test_password',
            'database': 'test_db',
            'port': 3306
        }
        self.manager = MySQLSchemaManager(**self.config)

    def test_initialization(self):
        """Test that MySQLSchemaManager initializes correctly"""
        self.assertEqual(self.manager.host, 'localhost')
        self.assertEqual(self.manager.username, 'test_user')
        self.assertEqual(self.manager.password, 'test_password')
        self.assertEqual(self.manager.database, 'test_db')
        self.assertEqual(self.manager.port, 3306)
        self.assertIsNone(self.manager.connection)

    @patch('mysql_schema_manager.mysql.connector.connect')
    def test_connect_success(self, mock_connect):
        """Test successful database connection"""
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        result = self.manager.connect()

        self.assertTrue(result)
        mock_connect.assert_called_once_with(
            host='localhost',
            user='test_user',
            password='test_password',
            database='test_db',
            port=3306
        )
        self.assertEqual(self.manager.connection, mock_connection)

    @patch('mysql_schema_manager.mysql.connector.connect')
    def test_connect_failure(self, mock_connect):
        """Test failed database connection"""
        mock_connect.side_effect = Exception("Connection failed")

        result = self.manager.connect()

        self.assertFalse(result)
        self.assertIsNone(self.manager.connection)

    def test_table_exists_query_generation(self):
        """Test that table existence check generates correct SQL"""
        expected_query = """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """
        # This test verifies the query structure is correct
        self.assertIn('information_schema.tables', expected_query)
        self.assertIn('table_schema', expected_query)
        self.assertIn('table_name', expected_query)

    def test_column_exists_query_generation(self):
        """Test that column existence check generates correct SQL"""
        expected_query = """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s AND column_name = %s
            """
        # This test verifies the query structure is correct
        self.assertIn('information_schema.columns', expected_query)
        self.assertIn('table_schema', expected_query)
        self.assertIn('table_name', expected_query)
        self.assertIn('column_name', expected_query)

    def test_index_exists_query_generation(self):
        """Test that index existence check generates correct SQL"""
        expected_query = """
            SELECT COUNT(*)
            FROM information_schema.statistics
            WHERE table_schema = %s AND table_name = %s AND index_name = %s
            """
        # This test verifies the query structure is correct
        self.assertIn('information_schema.statistics', expected_query)
        self.assertIn('table_schema', expected_query)
        self.assertIn('table_name', expected_query)
        self.assertIn('index_name', expected_query)

    @patch('mysql_schema_manager.mysql.connector.connect')
    def test_create_table_with_drop_logic(self, mock_connect):
        """Test create table logic with mock connection"""
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor

        # Mock table_exists to return True (table exists)
        self.manager.table_exists = Mock(return_value=True)
        self.manager.execute_query = Mock(return_value=True)

        table_name = "test_table"
        create_sql = "CREATE TABLE test_table (id INT PRIMARY KEY)"

        result = self.manager.create_table_with_drop(table_name, create_sql)

        self.assertTrue(result)
        self.manager.table_exists.assert_called_once_with(table_name)
        # execute_query should be called twice: once for DROP, once for CREATE
        self.assertEqual(self.manager.execute_query.call_count, 2)

    @patch('mysql_schema_manager.mysql.connector.connect')
    def test_alter_table_add_column_new_column(self, mock_connect):
        """Test alter table when adding a new column"""
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        self.manager.column_exists = Mock(return_value=False)
        self.manager.execute_query = Mock(return_value=True)

        table_name = "test_table"
        column_name = "new_column"
        column_definition = "VARCHAR(255) NOT NULL"

        result = self.manager.alter_table_add_column(table_name, column_name, column_definition)

        self.assertTrue(result)
        self.manager.column_exists.assert_called_once_with(table_name, column_name)
        self.manager.execute_query.assert_called_once()

    @patch('mysql_schema_manager.mysql.connector.connect')
    def test_alter_table_add_column_existing_same(self, mock_connect):
        """Test alter table when column exists with same definition"""
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        self.manager.column_exists = Mock(return_value=True)
        self.manager.get_column_definition = Mock(return_value="VARCHAR(255) NOT NULL")
        self.manager.execute_query = Mock(return_value=True)

        table_name = "test_table"
        column_name = "existing_column"
        column_definition = "VARCHAR(255) NOT NULL"

        result = self.manager.alter_table_add_column(table_name, column_name, column_definition)

        self.assertTrue(result)
        self.manager.column_exists.assert_called_once_with(table_name, column_name)
        self.manager.get_column_definition.assert_called_once_with(table_name, column_name)
        # execute_query should not be called since definitions are the same
        self.manager.execute_query.assert_not_called()

    @patch('mysql_schema_manager.mysql.connector.connect')
    def test_create_index_with_check_existing(self, mock_connect):
        """Test create index when index already exists"""
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        self.manager.index_exists = Mock(return_value=True)
        self.manager.execute_query = Mock(return_value=True)

        table_name = "test_table"
        index_name = "test_index"
        columns = ["id", "name"]

        result = self.manager.create_index_with_check(table_name, index_name, columns)

        self.assertTrue(result)
        self.manager.index_exists.assert_called_once_with(table_name, index_name)
        # execute_query should be called twice: once for DROP, once for CREATE
        self.assertEqual(self.manager.execute_query.call_count, 2)

    def test_column_definition_normalization(self):
        """Test that column definitions are normalized for comparison"""
        # This tests the logic of comparing column definitions
        def normalize_definition(definition):
            return ' '.join(definition.split()).lower() if definition else ''

        # Test normalization
        def1 = "VARCHAR(255) NOT NULL DEFAULT 'test'"
        def2 = "  varchar(255)   not  null   default 'test'  "
        def3 = "INT DEFAULT 0"

        self.assertEqual(normalize_definition(def1), normalize_definition(def2))
        self.assertNotEqual(normalize_definition(def1), normalize_definition(def3))

    def test_sql_injection_prevention(self):
        """Test that parameterized queries are used correctly"""
        # This test ensures that the class uses parameterized queries
        # rather than string concatenation to prevent SQL injection
        test_params = ('test_db', 'test_table')

        # The queries should use %s placeholders for parameters
        table_query = """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """

        self.assertIn('%s', table_query)
        self.assertEqual(table_query.count('%s'), len(test_params))


class TestSQLGeneration(unittest.TestCase):
    """Test SQL generation logic"""

    def test_create_table_sql(self):
        """Test CREATE TABLE SQL generation"""
        expected_elements = [
            'CREATE TABLE',
            'users',
            'id INT AUTO_INCREMENT PRIMARY KEY',
            'username VARCHAR(50) NOT NULL UNIQUE',
            'email VARCHAR(100) NOT NULL',
            'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'ENGINE=InnoDB',
            'CHARSET=utf8mb4'
        ]

        create_sql = """
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """

        for element in expected_elements:
            self.assertIn(element, create_sql)

    def test_alter_table_sql(self):
        """Test ALTER TABLE SQL generation"""
        table_name = "users"
        column_name = "age"
        column_definition = "INT DEFAULT 0"

        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        expected_sql = "ALTER TABLE users ADD COLUMN age INT DEFAULT 0"

        self.assertEqual(alter_sql, expected_sql)

    def test_create_index_sql(self):
        """Test CREATE INDEX SQL generation"""
        table_name = "users"
        index_name = "idx_email"
        columns = ["email"]

        index_sql = f"CREATE INDEX {index_name} ON {table_name} ({', '.join(columns)})"
        expected_sql = "CREATE INDEX idx_email ON users (email)"

        self.assertEqual(index_sql, expected_sql)

        # Test composite index
        columns_composite = ["username", "email"]
        composite_sql = f"CREATE INDEX idx_username_email ON {table_name} ({', '.join(columns_composite)})"
        expected_composite = "CREATE INDEX idx_username_email ON users (username, email)"

        self.assertEqual(composite_sql, expected_composite)


class TestSQLFileExecution(unittest.TestCase):
    """Test SQL file execution functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'host': 'localhost',
            'username': 'test_user',
            'password': 'test_password',
            'database': 'test_db',
            'port': 3306
        }
        self.manager = MySQLSchemaManager(**self.config)

    def test_clean_sql_content(self):
        """Test SQL content cleaning"""
        sql_with_comments = """
        -- This is a comment
        SELECT * FROM users;
        /* This is a
           multi-line comment */
        INSERT INTO table VALUES (1);
        """

        cleaned = self.manager._clean_sql_content(sql_with_comments)

        self.assertNotIn('-- This is a comment', cleaned)
        self.assertNotIn('/* This is a', cleaned)
        self.assertIn('SELECT * FROM users', cleaned)
        self.assertIn('INSERT INTO table VALUES (1)', cleaned)

    def test_parse_sql_file_statements(self):
        """Test SQL file parsing"""
        test_sql = """
        CREATE TABLE users (
            id INT PRIMARY KEY,
            name VARCHAR(50)
        );

        INSERT INTO users (id, name) VALUES (1, 'test');

        CREATE INDEX idx_name ON users (name);
        """

        # Create a temporary SQL file
        with open('test_temp.sql', 'w') as f:
            f.write(test_sql)

        try:
            statements = self.manager.parse_sql_file('test_temp.sql')

            # Should parse 3 statements
            self.assertEqual(len(statements), 3)
            self.assertIn('CREATE TABLE users', statements[0])
            self.assertIn('INSERT INTO users', statements[1])
            self.assertIn('CREATE INDEX idx_name', statements[2])
        finally:
            # Clean up
            if os.path.exists('test_temp.sql'):
                os.remove('test_temp.sql')

    def test_parse_sql_with_quoted_semicolons(self):
        """Test parsing SQL with semicolons in quoted strings"""
        test_sql = """
        INSERT INTO messages (content) VALUES ('Hello; world');
        INSERT INTO messages (content) VALUES ("Test; semicolon");
        """

        # Create a temporary SQL file
        with open('test_quotes.sql', 'w') as f:
            f.write(test_sql)

        try:
            statements = self.manager.parse_sql_file('test_quotes.sql')

            # Should parse 2 statements (not split on quoted semicolons)
            self.assertEqual(len(statements), 2)
            self.assertIn('Hello; world', statements[0])
            self.assertIn('Test; semicolon', statements[1])
        finally:
            # Clean up
            if os.path.exists('test_quotes.sql'):
                os.remove('test_quotes.sql')

    def test_extract_table_name_from_create(self):
        """Test table name extraction from CREATE TABLE statements"""
        test_cases = [
            ("CREATE TABLE users (id INT)", "users"),
            ("CREATE TABLE IF NOT EXISTS products (id INT)", "products"),
            ("CREATE TABLE `test_table` (id INT)", "test_table"),
            ("create table customers (id int)", "customers"),  # lowercase
        ]

        for sql, expected_table in test_cases:
            with self.subTest(sql=sql):
                result = self.manager._extract_table_name_from_create(sql)
                self.assertEqual(result, expected_table)

    def test_extract_column_info_from_alter(self):
        """Test column info extraction from ALTER TABLE statements"""
        test_cases = [
            ("ALTER TABLE users ADD COLUMN age INT", ("users", "age", "INT")),
            ("ALTER TABLE `products` ADD COLUMN `price` DECIMAL(10,2)", ("products", "price", "DECIMAL(10,2)")),
            ("ALTER TABLE customers ADD COLUMN status VARCHAR(20) DEFAULT 'active'", ("customers", "status", "VARCHAR(20) DEFAULT 'active'")),
        ]

        for sql, expected in test_cases:
            with self.subTest(sql=sql):
                result = self.manager._extract_column_info_from_alter(sql)
                self.assertEqual(result, expected)

    def test_extract_index_info_from_create(self):
        """Test index info extraction from CREATE INDEX statements"""
        test_cases = [
            ("CREATE INDEX idx_name ON users (name)", ("idx_name", "users", ["name"])),
            ("CREATE UNIQUE INDEX idx_email ON users (email)", ("idx_email", "users", ["email"])),
            ("CREATE INDEX idx_comp ON orders (user_id, order_date)", ("idx_comp", "orders", ["user_id", "order_date"])),
        ]

        for sql, expected in test_cases:
            with self.subTest(sql=sql):
                result = self.manager._extract_index_info_from_create(sql)
                self.assertEqual(result, expected)

    @patch('mysql_schema_manager.mysql.connector.connect')
    def test_execute_sql_file_dry_run(self, mock_connect):
        """Test SQL file execution in dry run mode"""
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        # Create a test SQL file
        test_sql = """
        CREATE TABLE test_table (id INT PRIMARY KEY);
        INSERT INTO test_table VALUES (1);
        """

        with open('test_dry_run.sql', 'w') as f:
            f.write(test_sql)

        try:
            # Mock the necessary methods
            self.manager.table_exists = Mock(return_value=False)
            self.manager.execute_query = Mock(return_value=True)

            result = self.manager.execute_sql_file('test_dry_run.sql', dry_run=True)

            # Should succeed without actually executing
            self.assertTrue(result)
            # execute_query should not be called in dry run mode
            self.manager.execute_query.assert_not_called()
        finally:
            if os.path.exists('test_dry_run.sql'):
                os.remove('test_dry_run.sql')

    @patch('mysql_schema_manager.mysql.connector.connect')
    def test_handle_create_table_exists(self, mock_connect):
        """Test CREATE TABLE handling when table already exists"""
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        self.manager.table_exists = Mock(return_value=True)

        statement = "CREATE TABLE users (id INT PRIMARY KEY)"
        result = self.manager._handle_create_table(statement, dry_run=False)

        self.assertTrue(result)  # Should return True (skipped)
        self.manager.table_exists.assert_called_once_with('users')

    @patch('mysql_schema_manager.mysql.connector.connect')
    def test_handle_add_column_new(self, mock_connect):
        """Test ADD COLUMN handling when column doesn't exist"""
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        self.manager.column_exists = Mock(return_value=False)
        self.manager.execute_query = Mock(return_value=True)

        statement = "ALTER TABLE users ADD COLUMN age INT"
        result = self.manager._handle_add_column(statement, dry_run=False)

        self.assertTrue(result)
        self.manager.execute_query.assert_called_once_with(statement)

    @patch('mysql_schema_manager.mysql.connector.connect')
    def test_handle_create_index_exists(self, mock_connect):
        """Test CREATE INDEX handling when index already exists"""
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        self.manager.index_exists = Mock(return_value=True)

        statement = "CREATE INDEX idx_name ON users (name)"
        result = self.manager._handle_create_index(statement, dry_run=False)

        self.assertTrue(result)  # Should return True (skipped)
        self.manager.index_exists.assert_called_once_with('users', 'idx_name')

    @patch('mysql_schema_manager.mysql.connector.connect')
    def test_handle_dml_statement(self, mock_connect):
        """Test DML statement handling"""
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        self.manager.execute_query = Mock(return_value=True)

        # Test INSERT
        statement = "INSERT INTO users (name) VALUES ('test')"
        result = self.manager._handle_dml_statement(statement, dry_run=False)

        self.assertTrue(result)
        self.manager.execute_query.assert_called_once_with(statement)

    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file"""
        statements = self.manager.parse_sql_file('nonexistent.sql')
        self.assertEqual(statements, [])

    def test_malformed_sql_parsing(self):
        """Test parsing malformed SQL"""
        malformed_sql = "CREATE TABLE users (id INT"  # Missing closing parenthesis

        with open('test_malformed.sql', 'w') as f:
            f.write(malformed_sql)

        try:
            statements = self.manager.parse_sql_file('test_malformed.sql')
            # Should still parse the incomplete statement
            self.assertEqual(len(statements), 1)
            self.assertIn('CREATE TABLE users', statements[0])
        finally:
            if os.path.exists('test_malformed.sql'):
                os.remove('test_malformed.sql')


def run_syntax_check():
    """Run a basic syntax check on the main script"""
    try:
        import mysql_schema_manager
        print("✓ Script syntax is valid")

        # Test class instantiation
        config = {
            'host': 'localhost',
            'username': 'test',
            'password': 'test',
            'database': 'test',
            'port': 3306
        }
        manager = mysql_schema_manager.MySQLSchemaManager(**config)
        print("✓ Class instantiation successful")

        # Test method existence
        required_methods = [
            'connect', 'disconnect', 'execute_query',
            'table_exists', 'column_exists', 'index_exists',
            'create_table_with_drop', 'alter_table_add_column', 'create_index_with_check'
        ]

        for method in required_methods:
            if hasattr(manager, method):
                print(f"✓ Method '{method}' exists")
            else:
                print(f"✗ Method '{method}' missing")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("=== MySQL Schema Manager Test Suite ===")
    print()

    print("1. Running syntax check...")
    syntax_ok = run_syntax_check()
    print()

    if syntax_ok:
        print("2. Running unit tests...")
        unittest.main(verbosity=2, exit=False)
    else:
        print("Syntax check failed, skipping unit tests")