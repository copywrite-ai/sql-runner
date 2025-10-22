#!/usr/bin/env python3
"""
Simple script to execute SQL files with idempotent safety
Usage:
    python execute_sql.py file.sql [--dry-run]
"""

import argparse
import os
import sys
from mysql_schema_manager import MySQLSchemaManager


def main():
    parser = argparse.ArgumentParser(description='Execute SQL files with idempotent safety')
    parser.add_argument('sql_file', help='SQL file to execute')
    parser.add_argument('--dry-run', action='store_true', help='Preview what would be executed without making changes')
    parser.add_argument('--host', default='localhost', help='MySQL host (default: localhost)')
    parser.add_argument('--user', default='root', help='MySQL username (default: root)')
    parser.add_argument('--password', default='', help='MySQL password')
    parser.add_argument('--database', required=True, help='MySQL database name')
    parser.add_argument('--port', type=int, default=3306, help='MySQL port (default: 3306)')

    args = parser.parse_args()

    # Validate SQL file exists
    if not os.path.exists(args.sql_file):
        print(f"Error: SQL file '{args.sql_file}' not found")
        sys.exit(1)

    # Create schema manager
    config = {
        'host': args.host,
        'username': args.user,
        'password': args.password,
        'database': args.database,
        'port': args.port
    }

    manager = MySQLSchemaManager(**config)

    try:
        # Connect to database
        if not manager.connect():
            print("Error: Failed to connect to database")
            sys.exit(1)

        print(f"Connected to database '{args.database}' on {args.host}:{args.port}")

        # Execute SQL file
        if args.dry_run:
            print(f"\n=== DRY RUN MODE - Previewing {args.sql_file} ===")
        else:
            print(f"\n=== Executing {args.sql_file} ===")

        success = manager.execute_sql_file(args.sql_file, dry_run=args.dry_run)

        if success:
            print(f"\n✓ SQL file executed successfully")
        else:
            print(f"\n✗ SQL file execution failed")
            sys.exit(1)

    finally:
        manager.disconnect()
        print("Database connection closed")


if __name__ == "__main__":
    main()