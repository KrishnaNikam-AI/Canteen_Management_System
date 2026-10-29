"""
tests/test_web_app.py
=====================
Automated tests for Canteen Management System Web Application.
Validates HTTP routing, HTML templates, static asset delivery,
JSON API formats, and error handling.
"""

import sys
from pathlib import Path
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from web.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestWebPages:
    """Tests all HTML view rendering."""

    @pytest.mark.parametrize(
        "route,expected_title",
        [
            ("/", "Dashboard"),
            ("/categories", "Categories"),
            ("/menu", "Menu Items"),
            ("/menu-items", "Menu Items"),
            ("/customers", "Customers"),
            ("/employees", "Employees"),
            ("/orders", "Orders & POS"),
            ("/payments", "Payments"),
            ("/reports", "Reports"),
        ],
    )
    def test_page_renders_successfully(self, client, route, expected_title):
        response = client.get(route)
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert expected_title in html
        assert "data-theme" in html
        assert "sidebar" in html

    def test_static_assets_available(self, client):
        css = client.get("/static/style.css")
        assert css.status_code == 200
        assert "var(--bg-app)" in css.get_data(as_text=True)

        js = client.get("/static/app.js")
        assert js.status_code == 200
        assert "toggleTheme" in js.get_data(as_text=True)


class TestWebApiEndpoints:
    """Tests JSON API endpoints."""

    def test_allowed_transitions_endpoint(self, client):
        res = client.get("/api/orders/allowed-transitions")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert "Pending" in data["data"]
        assert "Preparing" in data["data"]["Pending"]

    def test_unknown_route_returns_404(self, client):
        res = client.get("/non-existent-route-xyz")
        assert res.status_code == 404

    def test_create_category_empty_payload_fails(self, client):
        res = client.post("/api/categories", json={})
        assert res.status_code in (400, 500)
        data = res.get_json()
        assert data["success"] is False
