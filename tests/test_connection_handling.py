"""
tests/test_connection_handling.py
=================================
Automated verification for database connection error handling:
- Successful connection
- Wrong credentials error handling (1045)
- Server unreachable / not running error handling (2003)
- Non-existent database error handling (1049)
- Verifying friendly diagnostic messages
"""

import sys
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.connection import test_connection as check_db_connection, get_connection
from config.config import get_db_config


def test_successful_connection():
    ok, msg = check_db_connection()
    print("Test 1 - Live Connection:", "PASS" if ok else "FAIL", msg)
    assert ok is True, f"Live database connection failed: {msg}"


def test_wrong_credentials_handling():
    with patch("db.connection.get_db_config") as mock_cfg:
        cfg = get_db_config(include_database=True)
        cfg["user"] = "invalid_user_access_denied"
        cfg["password"] = "wrong_password_12345"
        mock_cfg.return_value = cfg

        try:
            get_connection(include_database=True)
            assert False, "Should have raised ConnectionError on wrong credentials"
        except ConnectionError as ce:
            msg = str(ce)
            print("Test 2 - Wrong Authentication Message:", msg)
            assert "1045" in msg or "Authentication Failed" in msg, "Friendly error message should mention 1045/auth"
            assert ".env" in msg, "Friendly error message should guide user to .env file"


def test_server_unreachable_handling():
    with patch("db.connection.get_db_config") as mock_cfg:
        cfg = get_db_config(include_database=True)
        cfg["port"] = 59999  # Inactive port to simulate MySQL not running
        mock_cfg.return_value = cfg

        try:
            get_connection(include_database=True)
            assert False, "Should have raised ConnectionError when MySQL server is unreachable"
        except ConnectionError as ce:
            msg = str(ce)
            print("Test 3 - Server Unreachable Message:", msg)
            assert "Server Unreachable" in msg or "Could not reach MySQL" in msg, (
                "Friendly error message should guide user that server is unreachable"
            )
            assert "XAMPP" in msg or "port" in msg, "Friendly error message should guide user to check XAMPP/port"


def test_missing_database_handling():
    with patch("db.connection.get_db_config") as mock_cfg:
        cfg = get_db_config(include_database=True)
        cfg["database"] = "definitely_non_existent_canteen_db_xyz"
        mock_cfg.return_value = cfg

        try:
            get_connection(include_database=True)
            assert False, "Should have raised ConnectionError on missing database"
        except ConnectionError as ce:
            msg = str(ce)
            print("Test 4 - Missing Database Message:", msg)
            assert "1049" in msg or "Database Missing" in msg, "Friendly error message should mention missing DB"
            assert "init_db.py" in msg, "Friendly error message should guide user to run init_db.py"


if __name__ == "__main__":
    test_successful_connection()
    test_wrong_credentials_handling()
    test_server_unreachable_handling()
    test_missing_database_handling()
    print("\nALL DATABASE CONNECTION TESTS PASSED WITH FRIENDLY ERROR MESSAGES!")
