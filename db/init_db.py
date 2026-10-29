"""
db/init_db.py
=============
Database Initialization Script for Canteen Management System.
Executes 'database/schema.sql' and 'database/sample_data.sql' statement by statement.
Compatible with both CMySQLCursor and pure-Python MySQL/MariaDB cursors.

Usage:
    python -m db.init_db
"""

import sys
from pathlib import Path
from typing import Dict, List

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.connection import get_connection, MySQLError


def split_sql_statements(sql_text: str) -> List[str]:
    """
    Parses a SQL script into individual executable statements,
    stripping single-line comments, block comments, and empty lines.
    """
    statements = []
    current_statement = []

    for line in sql_text.splitlines():
        stripped = line.strip()
        # Skip comment lines and blank lines
        if not stripped or stripped.startswith("--") or stripped.startswith("/*"):
            continue

        current_statement.append(line)
        # Semicolon marks the completion of a statement
        if stripped.endswith(";"):
            statement_str = "\n".join(current_statement).strip()
            # Remove trailing semicolon for execute
            if statement_str.endswith(";"):
                statement_str = statement_str[:-1].strip()
            if statement_str:
                statements.append(statement_str)
            current_statement = []

    return statements


def execute_sql_file(connection, file_path: Path) -> int:
    """
    Executes all SQL commands from a .sql file sequentially.

    Args:
        connection: Active MySQL database connection.
        file_path (Path): Path to the .sql file.

    Returns:
        int: Number of statements executed.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"SQL file not found at: {file_path}")

    print(f"Executing: {file_path.name} ...")
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    statements = split_sql_statements(sql_content)
    cursor = connection.cursor()
    try:
        for idx, stmt in enumerate(statements, start=1):
            cursor.execute(stmt)
        connection.commit()
        print(f"Successfully executed: {file_path.name} ({len(statements)} statements)")
        return len(statements)
    finally:
        cursor.close()


def verify_table_counts(connection) -> Dict[str, int]:
    """
    Queries row counts for all 7 tables in canteen_db to verify data loading.
    """
    tables = [
        "categories",
        "menu_items",
        "customers",
        "employees",
        "orders",
        "order_items",
        "payments",
    ]
    counts = {}
    cursor = connection.cursor()
    try:
        cursor.execute("USE canteen_db;")
        for tbl in tables:
            cursor.execute(f"SELECT COUNT(*) FROM `{tbl}`;")
            (count,) = cursor.fetchone()
            counts[tbl] = count
    finally:
        cursor.close()
    return counts


def initialize_database(load_sample_data: bool = True) -> Dict[str, int]:
    """
    Creates canteen_db, initializes the 7 relational tables,
    and optionally populates consistent sample records.

    Returns:
        Dict[str, int]: Dictionary of table row counts upon completion.
    """
    database_dir = ROOT_DIR / "database"
    schema_path = database_dir / "schema.sql"
    sample_data_path = database_dir / "sample_data.sql"

    print("Connecting to MySQL server...")
    # Connect initially without specifying database so CREATE DATABASE can run
    conn = get_connection(include_database=False)

    try:
        # 1. Execute schema.sql (Database, 7 tables, constraints, indexes)
        execute_sql_file(conn, schema_path)

        # 2. Execute sample_data.sql (Realistic sample dataset)
        if load_sample_data and sample_data_path.exists():
            execute_sql_file(conn, sample_data_path)

        # 3. Verify row counts
        row_counts = verify_table_counts(conn)
        print("\n========================================")
        print("  Database Table Verification Summary   ")
        print("========================================")
        for tbl, count in row_counts.items():
            print(f"  * {tbl:<15} : {count:>3} rows")
        print("========================================")
        print("Database initialization completed successfully!\n")
        return row_counts
    except MySQLError as err:
        print(f"\n[MySQL Error during initialization]: {err}", file=sys.stderr)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("========================================")
    print(" Canteen Management System - DB Setup   ")
    print("========================================")
    try:
        initialize_database(load_sample_data=True)
    except Exception as exc:
        print(f"\nSetup failed: {exc}", file=sys.stderr)
        sys.exit(1)
