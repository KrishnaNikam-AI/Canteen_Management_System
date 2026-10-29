"""
db/connection.py
================
MySQL Database Connection Manager and Query Execution Helpers.

College Viva Concepts:
1. Parameterized Queries: All SQL queries use '%s' placeholders to prevent SQL Injection attacks.
2. Connection Management: Every helper cleanly opens and closes cursors and connections.
3. Transaction Control: Commits persist state changes; rollbacks safeguard integrity on error.
"""

from contextlib import contextmanager
from typing import Generator, Tuple, List, Dict, Any, Optional
from config.config import get_db_config

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    mysql = None
    MySQLError = Exception


def get_connection(include_database: bool = True):
    """
    Creates and returns a new MySQL database connection using configuration from config.py.

    Args:
        include_database (bool): If True, connects directly to canteen_db.

    Returns:
        MySQL connection instance.

    Raises:
        RuntimeError: If mysql-connector-python is not installed.
        MySQLError: If connection to MySQL server fails.
    """
    if mysql is None:
        raise RuntimeError(
            "mysql-connector-python is not installed. "
            "Please run: pip install -r requirements.txt"
        )

    config = get_db_config(include_database=include_database)
    try:
        return mysql.connector.connect(**config)
    except MySQLError as err:
        errno = getattr(err, "errno", None)
        host = config.get("host", "localhost")
        port = config.get("port", 3306)
        user = config.get("user", "root")
        db = config.get("database", "canteen_db")

        if errno == 1045:
            friendly_msg = (
                f"[Authentication Failed (Error 1045)]: Access denied for user '{user}'. "
                "Please verify your DB_USER and DB_PASSWORD in the .env file. "
                "(Note: Default XAMPP MySQL uses user 'root' with an empty password: DB_PASSWORD=)."
            )
        elif errno in (2002, 2003, 2005):
            friendly_msg = (
                f"[Server Unreachable (Error {errno})]: Could not reach MySQL server at {host}:{port}. "
                "Please verify that MySQL is running (e.g., start the MySQL module in the XAMPP Control Panel) "
                "and listening on port 3306."
            )
        elif errno == 1049:
            friendly_msg = (
                f"[Database Missing (Error 1049)]: Database '{db}' does not exist on {host}:{port}. "
                "Please initialize it first by running: python db/init_db.py"
            )
        else:
            friendly_msg = (
                f"[Database Connection Error {errno}]: Could not connect to MySQL server at {host}:{port}. "
                f"Details: {err.msg}"
            )
        raise ConnectionError(friendly_msg) from err


@contextmanager
def get_db_cursor(commit: bool = False, dictionary: bool = True) -> Generator:
    """
    Context manager yielding (connection, cursor) that automatically commits on success,
    rolls back on unhandled exceptions, and safely closes both cursor and connection.
    """
    conn = get_connection(include_database=True)
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield conn, cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def test_connection() -> Tuple[bool, str]:
    """
    Tests whether the application can successfully connect to the MySQL database.

    Returns:
        Tuple[bool, str]: (True, version_string) or (False, error_description)
    """
    if mysql is None:
        return False, "mysql-connector-python library is not installed."

    try:
        conn = get_connection(include_database=True)
        if conn.is_connected():
            server_info = getattr(conn, "server_info", "Active")
            conn.close()
            return True, f"Successfully connected to MySQL/MariaDB version {server_info}"
        return False, "Could not establish connection to MySQL."
    except Exception as exc:
        return False, f"Database Connection Failed: {str(exc)}"


def fetch_all(query: str, params: Optional[tuple] = None, dictionary: bool = True) -> List[Dict[str, Any]]:
    """
    Executes a SELECT query with parameters and returns all matching rows.

    Args:
        query (str): Parameterized SQL query using %s placeholders.
        params (tuple, optional): Tuple of query parameters.
        dictionary (bool): If True, returns rows as dictionaries.

    Returns:
        List[Dict[str, Any]]: List of row records (empty list if no records found).
    """
    with get_db_cursor(commit=False, dictionary=dictionary) as (_, cursor):
        cursor.execute(query, params or ())
        return cursor.fetchall() or []


def fetch_one(query: str, params: Optional[tuple] = None, dictionary: bool = True) -> Optional[Dict[str, Any]]:
    """
    Executes a SELECT query with parameters and returns the first matching row.

    Args:
        query (str): Parameterized SQL query using %s placeholders.
        params (tuple, optional): Tuple of query parameters.
        dictionary (bool): If True, returns row as dictionary.

    Returns:
        Optional[Dict[str, Any]]: Matching row dictionary, or None if no record found.
    """
    with get_db_cursor(commit=False, dictionary=dictionary) as (_, cursor):
        cursor.execute(query, params or ())
        return cursor.fetchone()


def execute(query: str, params: Optional[tuple] = None, commit: bool = True) -> int:
    """
    Executes an INSERT, UPDATE, or DELETE query with %s parameters.

    Args:
        query (str): Parameterized SQL statement.
        params (tuple, optional): Tuple of values to bind to %s placeholders.
        commit (bool): Whether to commit the transaction immediately.

    Returns:
        int: The last inserted row ID (for INSERTs) or affected rows count.
    """
    with get_db_cursor(commit=commit, dictionary=True) as (_, cursor):
        cursor.execute(query, params or ())
        if cursor.lastrowid:
            return cursor.lastrowid
        return cursor.rowcount
