#!/usr/bin/env python3
"""
MySQL Schema Manager
A Python script for safe MySQL database schema operations with existence checking.
"""

import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Optional, Any
import logging
import os
import re

class MySQLSchemaManager:
    def __init__(self, host: str, username: str, password: str, database: str, port: int = 3306):
        """
        Initialize MySQL connection parameters

        Args:
            host: MySQL server host
            username: MySQL username
            password: MySQL password
            database: Database name
            port: MySQL port (default: 3306)
        """
        self.host = host
        self.username = username
        self.password = password
        self.database = database
        self.port = port
        self.connection = None

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """
        Establish database connection

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database,
                port=self.port
            )
            if self.connection.is_connected():
                self.logger.info(f"Successfully connected to MySQL database '{self.database}'")
                return True
        except (Error, Exception) as e:
            self.logger.error(f"Error connecting to MySQL: {e}")
            return False
        return False

    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.logger.info("MySQL connection closed")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """
        Execute a SQL query

        Args:
            query: SQL query to execute
            params: Optional parameters for prepared statements

        Returns:
            bool: True if execution successful, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            cursor.close()
            self.logger.info(f"Query executed successfully: {query}")
            return True
        except Error as e:
            self.logger.error(f"Error executing query '{query}': {e}")
            self.connection.rollback()
            return False

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database

        Args:
            table_name: Name of the table to check

        Returns:
            bool: True if table exists, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            query = """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """
            cursor.execute(query, (self.database, table_name))
            result = cursor.fetchone()[0]
            cursor.close()
            return result > 0
        except Error as e:
            self.logger.error(f"Error checking table existence: {e}")
            return False

    def create_table_with_drop(self, table_name: str, create_table_sql: str) -> bool:
        """
        Create a table, dropping it first if it exists

        Args:
            table_name: Name of the table to create
            create_table_sql: Complete CREATE TABLE SQL statement

        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            if self.table_exists(table_name):
                self.logger.info(f"Table '{table_name}' exists, dropping it first")
                drop_query = f"DROP TABLE IF EXISTS {table_name}"
                if not self.execute_query(drop_query):
                    return False

            self.logger.info(f"Creating table '{table_name}'")
            return self.execute_query(create_table_sql)

        except Exception as e:
            self.logger.error(f"Error in create_table_with_drop: {e}")
            return False

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """
        Check if a column exists in a table

        Args:
            table_name: Name of the table
            column_name: Name of the column to check

        Returns:
            bool: True if column exists, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            query = """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s AND column_name = %s
            """
            cursor.execute(query, (self.database, table_name, column_name))
            result = cursor.fetchone()[0]
            cursor.close()
            return result > 0
        except Error as e:
            self.logger.error(f"Error checking column existence: {e}")
            return False

    def get_column_definition(self, table_name: str, column_name: str) -> Optional[str]:
        """
        Get the full column definition from information_schema

        Args:
            table_name: Name of the table
            column_name: Name of the column

        Returns:
            str: Column definition string or None if not found
        """
        try:
            cursor = self.connection.cursor()
            query = """
            SELECT COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, EXTRA
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s AND column_name = %s
            """
            cursor.execute(query, (self.database, table_name, column_name))
            result = cursor.fetchone()
            cursor.close()

            if result:
                column_type, is_nullable, default, column_key, extra = result
                definition = column_type
                if is_nullable == 'NO':
                    definition += ' NOT NULL'
                if default is not None:
                    definition += f" DEFAULT {default}"
                if column_key == 'UNI':
                    definition += ' UNIQUE'
                if 'auto_increment' in extra:
                    definition += ' AUTO_INCREMENT'
                return definition
            return None
        except Error as e:
            self.logger.error(f"Error getting column definition: {e}")
            return None

    def alter_table_add_column(self, table_name: str, column_name: str, column_definition: str) -> bool:
        """
        Add a column to a table, removing it first if it exists with different definition

        Args:
            table_name: Name of the table
            column_name: Name of the column to add
            column_definition: Column definition (e.g., "VARCHAR(255) NOT NULL DEFAULT 'test'")

        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Check if column exists
            if self.column_exists(table_name, column_name):
                current_definition = self.get_column_definition(table_name, column_name)

                # Normalize definitions for comparison (remove extra spaces)
                current_clean = ' '.join(current_definition.split()) if current_definition else ''
                new_clean = ' '.join(column_definition.split())

                if current_clean.lower() == new_clean.lower():
                    self.logger.info(f"Column '{column_name}' already exists with same definition in table '{table_name}'")
                    return True
                else:
                    self.logger.info(f"Column '{column_name}' exists with different definition, dropping it first")
                    drop_query = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
                    if not self.execute_query(drop_query):
                        return False

            # Add the column
            add_query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            self.logger.info(f"Adding column '{column_name}' to table '{table_name}'")
            return self.execute_query(add_query)

        except Exception as e:
            self.logger.error(f"Error in alter_table_add_column: {e}")
            return False

    def index_exists(self, table_name: str, index_name: str) -> bool:
        """
        Check if an index exists in a table

        Args:
            table_name: Name of the table
            index_name: Name of the index to check

        Returns:
            bool: True if index exists, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            query = """
            SELECT COUNT(*)
            FROM information_schema.statistics
            WHERE table_schema = %s AND table_name = %s AND index_name = %s
            """
            cursor.execute(query, (self.database, table_name, index_name))
            result = cursor.fetchone()[0]
            cursor.close()
            return result > 0
        except Error as e:
            self.logger.error(f"Error checking index existence: {e}")
            return False

    def create_index_with_check(self, table_name: str, index_name: str, column_names: List[str],
                               index_type: str = 'INDEX', unique: bool = False) -> bool:
        """
        Create an index, dropping it first if it exists

        Args:
            table_name: Name of the table
            index_name: Name of the index
            column_names: List of column names for the index
            index_type: Type of index (INDEX, FULLTEXT, SPATIAL)
            unique: Whether to create a UNIQUE index

        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Check if index exists and drop it if it does
            if self.index_exists(table_name, index_name):
                self.logger.info(f"Index '{index_name}' exists, dropping it first")
                drop_query = f"DROP INDEX {index_name} ON {table_name}"
                if not self.execute_query(drop_query):
                    return False

            # Create the index
            columns_str = ', '.join(column_names)
            if unique and index_type.upper() == 'INDEX':
                create_query = f"CREATE UNIQUE INDEX {index_name} ON {table_name} ({columns_str})"
            else:
                create_query = f"CREATE {index_type} {index_name} ON {table_name} ({columns_str})"

            self.logger.info(f"Creating {index_type} '{index_name}' on table '{table_name}'")
            return self.execute_query(create_query)

        except Exception as e:
            self.logger.error(f"Error in create_index_with_check: {e}")
            return False

    def parse_sql_file(self, file_path: str) -> List[str]:
        """
        Parse SQL file and split into individual statements

        Args:
            file_path: Path to the SQL file

        Returns:
            List[str]: List of SQL statements
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"SQL file not found: {file_path}")
                return []

            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Remove comments and clean up the content
            content = self._clean_sql_content(content)

            # Split statements by semicolon
            statements = []
            current_statement = ""

            # Track if we're inside a string literal
            in_string = False
            string_char = None

            for i, char in enumerate(content):
                if char in ("'", '"') and (i == 0 or content[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None

                if char == ';' and not in_string:
                    current_statement = current_statement.strip()
                    if current_statement and not current_statement.upper().startswith(('USE ', '--')):
                        statements.append(current_statement)
                    current_statement = ""
                else:
                    current_statement += char

            # Add the last statement if it doesn't end with semicolon
            if current_statement.strip():
                current_statement = current_statement.strip()
                if current_statement and not current_statement.upper().startswith(('USE ', '--')):
                    statements.append(current_statement)

            self.logger.info(f"Parsed {len(statements)} SQL statements from {file_path}")
            return statements

        except Exception as e:
            self.logger.error(f"Error parsing SQL file {file_path}: {e}")
            return []

    def _clean_sql_content(self, content: str) -> str:
        """
        Clean SQL content by removing comments and normalizing whitespace

        Args:
            content: Raw SQL content

        Returns:
            str: Cleaned SQL content
        """
        # Remove single-line comments
        content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)

        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        # Replace multiple newlines with single newline
        content = re.sub(r'\n\s*\n', '\n', content)

        return content.strip()

    def _extract_table_name_from_create(self, create_sql: str) -> Optional[str]:
        """
        Extract table name from CREATE TABLE statement

        Args:
            create_sql: CREATE TABLE SQL statement

        Returns:
            str: Table name or None if not found
        """
        match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?', create_sql, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_column_info_from_alter(self, alter_sql: str) -> Optional[tuple]:
        """
        Extract table name and column info from ALTER TABLE statement

        Args:
            alter_sql: ALTER TABLE SQL statement

        Returns:
            tuple: (table_name, column_name, column_definition) or None if not found
        """
        # Match ALTER TABLE table_name ADD COLUMN column_name definition
        match = re.search(
            r'ALTER\s+TABLE\s+`?(\w+)`?\s+ADD\s+COLUMN\s+`?(\w+)`?\s+(.+?)(?:\s+;|$)',
            alter_sql,
            re.IGNORECASE
        )
        if match:
            return match.group(1), match.group(2), match.group(3).strip()
        return None

    def _extract_index_info_from_create(self, create_sql: str) -> Optional[tuple]:
        """
        Extract index info from CREATE INDEX statement

        Args:
            create_sql: CREATE INDEX SQL statement

        Returns:
            tuple: (index_name, table_name, columns) or None if not found
        """
        # Match CREATE [UNIQUE] INDEX index_name ON table_name (columns)
        match = re.search(
            r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+`?(\w+)`?\s+ON\s+`?(\w+)`?\s*\((.+?)\)',
            create_sql,
            re.IGNORECASE
        )
        if match:
            columns = [col.strip().strip('`') for col in match.group(3).split(',')]
            return match.group(1), match.group(2), columns
        return None

    def execute_sql_file(self, file_path: str, dry_run: bool = False) -> bool:
        """
        Execute SQL file with idempotent safety checks

        Args:
            file_path: Path to the SQL file
            dry_run: If True, only log what would be executed without actually running

        Returns:
            bool: True if execution successful, False otherwise
        """
        try:
            self.logger.info(f"Executing SQL file: {file_path}")

            if dry_run:
                self.logger.info("DRY RUN MODE - No changes will be made")

            statements = self.parse_sql_file(file_path)
            if not statements:
                self.logger.warning("No valid SQL statements found in file")
                return False

            success_count = 0
            skip_count = 0
            error_count = 0

            for i, statement in enumerate(statements, 1):
                try:
                    statement_upper = statement.upper().strip()

                    # Skip empty statements
                    if not statement.strip():
                        continue

                    # Log current statement
                    self.logger.info(f"Statement {i}/{len(statements)}: {statement[:100]}...")

                    # Handle different types of statements with idempotent checks
                    if statement_upper.startswith('CREATE TABLE'):
                        if self._handle_create_table(statement, dry_run):
                            success_count += 1
                        else:
                            error_count += 1

                    elif statement_upper.startswith('ALTER TABLE') and 'ADD COLUMN' in statement_upper:
                        if self._handle_add_column(statement, dry_run):
                            success_count += 1
                        else:
                            error_count += 1

                    elif statement_upper.startswith(('CREATE INDEX', 'CREATE UNIQUE INDEX')):
                        if self._handle_create_index(statement, dry_run):
                            success_count += 1
                        else:
                            error_count += 1

                    elif statement_upper.startswith(('INSERT', 'UPDATE', 'DELETE')):
                        # DML statements - execute directly (no idempotent check needed)
                        if self._handle_dml_statement(statement, dry_run):
                            success_count += 1
                        else:
                            error_count += 1

                    else:
                        # Other statements - execute directly
                        self.logger.info(f"Executing other statement type: {statement_upper[:50]}...")
                        if dry_run:
                            self.logger.info(f"[DRY RUN] Would execute: {statement}")
                            success_count += 1
                        elif self.execute_query(statement):
                            success_count += 1
                        else:
                            error_count += 1

                except Exception as e:
                    self.logger.error(f"Error processing statement {i}: {e}")
                    error_count += 1

            self.logger.info(f"SQL file execution completed. Success: {success_count}, Skipped: {skip_count}, Errors: {error_count}")
            return error_count == 0

        except Exception as e:
            self.logger.error(f"Error executing SQL file {file_path}: {e}")
            return False

    def _handle_create_table(self, statement: str, dry_run: bool) -> bool:
        """Handle CREATE TABLE statement with idempotent check"""
        table_name = self._extract_table_name_from_create(statement)
        if not table_name:
            self.logger.error("Could not extract table name from CREATE TABLE statement")
            return False

        if self.table_exists(table_name):
            self.logger.info(f"Table '{table_name}' already exists, skipping CREATE TABLE")
            return True

        if dry_run:
            self.logger.info(f"[DRY RUN] Would create table '{table_name}'")
            return True

        return self.execute_query(statement)

    def _handle_add_column(self, statement: str, dry_run: bool) -> bool:
        """Handle ALTER TABLE ADD COLUMN statement with idempotent check"""
        column_info = self._extract_column_info_from_alter(statement)
        if not column_info:
            self.logger.error("Could not parse ALTER TABLE ADD COLUMN statement")
            return False

        table_name, column_name, column_definition = column_info

        if self.column_exists(table_name, column_name):
            current_def = self.get_column_definition(table_name, column_name)
            current_clean = ' '.join(current_def.split()) if current_def else ''
            new_clean = ' '.join(column_definition.split())

            if current_clean.lower() == new_clean.lower():
                self.logger.info(f"Column '{column_name}' already exists in table '{table_name}' with same definition")
                return True
            else:
                self.logger.info(f"Column '{column_name}' exists in table '{table_name}' with different definition")
                if dry_run:
                    self.logger.info(f"[DRY RUN] Would drop and recreate column '{column_name}' in table '{table_name}'")
                    return True
                # Drop existing column and add new one
                if not self.execute_query(f"ALTER TABLE {table_name} DROP COLUMN {column_name}"):
                    return False

        if dry_run:
            self.logger.info(f"[DRY RUN] Would add column '{column_name}' to table '{table_name}'")
            return True

        return self.execute_query(statement)

    def _handle_create_index(self, statement: str, dry_run: bool) -> bool:
        """Handle CREATE INDEX statement with idempotent check"""
        index_info = self._extract_index_info_from_create(statement)
        if not index_info:
            self.logger.error("Could not parse CREATE INDEX statement")
            return False

        index_name, table_name, columns = index_info

        if self.index_exists(table_name, index_name):
            self.logger.info(f"Index '{index_name}' already exists on table '{table_name}', skipping CREATE INDEX")
            return True

        if dry_run:
            self.logger.info(f"[DRY RUN] Would create index '{index_name}' on table '{table_name}'")
            return True

        return self.execute_query(statement)

    def _handle_dml_statement(self, statement: str, dry_run: bool) -> bool:
        """Handle DML statements (INSERT, UPDATE, DELETE)"""
        if dry_run:
            self.logger.info(f"[DRY RUN] Would execute DML: {statement}")
            return True

        return self.execute_query(statement)


def main():
    """
    Example usage of MySQLSchemaManager
    """
    # Database connection parameters
    config = {
        'host': 'localhost',
        'username': 'root',
        'password': 'password',
        'database': 'test_db',
        'port': 3306
    }

    # Create schema manager instance
    manager = MySQLSchemaManager(**config)

    try:
        # Connect to database
        if not manager.connect():
            print("Failed to connect to database")
            return

        print("=== Example 1: Create Table with Drop ===")
        # Create table example
        create_table_sql = """
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        manager.create_table_with_drop('users', create_table_sql)

        print("\n=== Example 2: Alter Table Add Column ===")
        # Add column examples
        manager.alter_table_add_column('users', 'age', 'INT DEFAULT 0')
        manager.alter_table_add_column('users', 'status', 'VARCHAR(20) DEFAULT "active"')

        # Try to add same column with different definition
        manager.alter_table_add_column('users', 'age', 'VARCHAR(10) DEFAULT "unknown"')

        print("\n=== Example 3: Create Index ===")
        # Create index examples
        manager.create_index_with_check('users', 'idx_email', ['email'])
        manager.create_index_with_check('users', 'idx_username_email', ['username', 'email'])
        manager.create_index_with_check('users', 'idx_age', ['age'], unique=False)

        print("\nAll operations completed!")

    finally:
        # Always close the connection
        manager.disconnect()


if __name__ == "__main__":
    main()