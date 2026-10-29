"""
config/config.py
================
Central Configuration Manager for Canteen Management System.
Supports dynamic reloading so changes in .env are picked up immediately.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def reload_env():
    """Reloads environment variables from .env if present."""
    if load_dotenv:
        if ENV_PATH.exists():
            load_dotenv(dotenv_path=ENV_PATH, override=True)
        else:
            load_dotenv(override=True)


# Initial load
reload_env()


def get_db_config(include_database: bool = True) -> dict:
    """
    Returns fresh database configuration from environment variables.
    Automatically reloads .env so password edits take effect immediately.
    """
    reload_env()

    host = os.getenv("DB_HOST", "localhost").strip()
    try:
        port = int(os.getenv("DB_PORT", "3306").strip())
    except ValueError:
        port = 3306
    user = os.getenv("DB_USER", "root").strip()
    password = os.getenv("DB_PASSWORD", "").strip()
    database = os.getenv("DB_NAME", "canteen_db").strip()

    config = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
    }
    if include_database:
        config["database"] = database
    return config


def check_env_file_exists() -> bool:
    return ENV_PATH.is_file()


# Convenience exports
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = 3306
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "canteen_db")
APP_NAME = os.getenv("APP_NAME", "Canteen Management System")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DB_CONFIG = get_db_config()
