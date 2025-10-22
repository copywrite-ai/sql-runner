#!/usr/bin/env python3
"""
Validate SQL files without database connection
"""

from mysql_schema_manager import MySQLSchemaManager
import os

def validate_sql_file(file_path):
    """Validate SQL file parsing without database connection"""
    print(f"\n=== Validating {file_path} ===")

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    # Create manager (won't connect)
    manager = MySQLSchemaManager('localhost', 'test', 'test', 'test')

    try:
        # Parse the file
        statements = manager.parse_sql_file(file_path)

        print(f"📄 Parsed {len(statements)} statements:")

        for i, statement in enumerate(statements, 1):
            stmt_type = statement.strip().split()[0].upper() if statement.strip() else "EMPTY"
            stmt_preview = statement.replace('\n', ' ').strip()[:80]
            if len(stmt_preview) < len(statement.replace('\n', ' ').strip()):
                stmt_preview += "..."

            print(f"  {i:2d}. [{stmt_type}] {stmt_preview}")

            # Validate statement parsing
            if stmt_type == 'CREATE' and 'TABLE' in statement.upper():
                table_name = manager._extract_table_name_from_create(statement)
                if table_name:
                    print(f"      ✅ Extracted table name: {table_name}")
                else:
                    print(f"      ⚠️  Could not extract table name")

            elif stmt_type == 'ALTER' and 'ADD COLUMN' in statement.upper():
                column_info = manager._extract_column_info_from_alter(statement)
                if column_info:
                    table_name, column_name, column_def = column_info
                    print(f"      ✅ Extracted: {table_name}.{column_name} ({column_def[:50]}...)")
                else:
                    print(f"      ⚠️  Could not extract column info")

            elif stmt_type == 'CREATE' and 'INDEX' in statement.upper():
                index_info = manager._extract_index_info_from_create(statement)
                if index_info:
                    index_name, table_name, columns = index_info
                    print(f"      ✅ Extracted index: {index_name} on {table_name}({', '.join(columns)})")
                else:
                    print(f"      ⚠️  Could not extract index info")

        print(f"✅ Successfully validated {file_path}")
        return True

    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False

def main():
    print("=== SQL File Validation Tool ===")

    # Find all .sql files in current directory
    sql_files = [f for f in os.listdir('.') if f.endswith('.sql')]

    if not sql_files:
        print("No .sql files found in current directory")
        return

    print(f"Found {len(sql_files)} SQL files to validate:")

    success_count = 0
    for sql_file in sorted(sql_files):
        if validate_sql_file(sql_file):
            success_count += 1

    print(f"\n=== Summary ===")
    print(f"Validated: {success_count}/{len(sql_files)} files")

    if success_count == len(sql_files):
        print("🎉 All SQL files validated successfully!")
    else:
        print("⚠️  Some files had issues - please check the output above")

if __name__ == "__main__":
    main()