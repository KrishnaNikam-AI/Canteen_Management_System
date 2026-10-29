"""
main.py
=======
Modern Web Application Entry Point for Canteen Management System.
Powered by Flask, Jinja2, HTML5/CSS3, and Chart.js.

Running this script starts the local development web server and
automatically opens the dashboard in your default browser.
"""

import sys
import os
import threading
import time
import webbrowser
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from web.app import app
from db.connection import test_connection


def open_browser():
    """Wait for server to bind, then open the browser automatically."""
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    print("=" * 70)
    print("         CANTEEN MANAGEMENT SYSTEM - WEB APPLICATION")
    print("=" * 70)

    # Test database connectivity
    ok_db, msg = test_connection()
    if ok_db:
        print("  Database : ✅ Connected to MySQL")
    else:
        print(f"  Database : ⚠️ {msg}")

    print("  Local URL: http://127.0.0.1:5000")
    print("  Stop     : Press Ctrl+C in this terminal window")
    print("=" * 70)
    print()

    # Open browser only in the primary process (not the reloader child)
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Thread(target=open_browser, daemon=True).start()

    app.run(host="0.0.0.0", port=5000, debug=True)
