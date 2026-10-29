"""
tests/test_order_logic.py
=========================
Unit and Integration Tests for Order Logic, Status Transitions, and Payments.

Contains:
1. Pure Logic Tests (run completely in memory without a database).
2. Database-Dependent Integration Tests (clearly marked and skipped if MySQL is offline).
"""

import pytest
from services.order_service import (
    calculate_order_totals,
    ALLOWED_STATUS_TRANSITIONS,
)
from db.connection import test_connection as check_db_alive

# Check if a live MySQL connection is accessible
DB_OK, _ = check_db_alive()
skip_if_no_db = pytest.mark.skipif(
    not DB_OK, reason="Live MySQL database is not connected or offline."
)


# ==============================================================================
# 1. Pure Logic Tests (No Database Needed)
# ==============================================================================
class TestOrderCalculations:
    def test_single_item_total(self):
        items = [{"name": "Masala Dosa", "price": 55.00, "quantity": 2}]
        gross, discount, final = calculate_order_totals(items, discount_percent=0.0)
        assert gross == 110.00
        assert discount == 0.00
        assert final == 110.00

    def test_multiple_items_with_discount(self):
        items = [
            {"name": "Executive Thali", "price": 120.00, "quantity": 1},
            {"name": "Filter Coffee", "price": 20.00, "quantity": 2},
        ]
        # Gross = 120 + 40 = 160.00
        # 10% discount = 16.00, Final = 144.00
        gross, discount, final = calculate_order_totals(items, discount_percent=10.0)
        assert gross == 160.00
        assert discount == 16.00
        assert final == 144.00

    def test_empty_cart_returns_zero(self):
        gross, discount, final = calculate_order_totals([], discount_percent=5.0)
        assert gross == 0.00
        assert discount == 0.00
        assert final == 0.00

    def test_negative_discount_raises_error(self):
        with pytest.raises(ValueError, match="between 0 and 100"):
            calculate_order_totals([], discount_percent=-5.0)

    def test_over_100_discount_raises_error(self):
        with pytest.raises(ValueError, match="between 0 and 100"):
            calculate_order_totals([], discount_percent=105.0)

    def test_negative_item_price_raises_error(self):
        with pytest.raises(ValueError, match="non-negative"):
            calculate_order_totals([{"price": -10.00, "quantity": 1}])

    def test_negative_item_quantity_raises_error(self):
        with pytest.raises(ValueError, match="non-negative"):
            calculate_order_totals([{"price": 10.00, "quantity": -2}])


class TestStatusTransitionMatrix:
    """Tests the state machine transition definitions."""

    def test_pending_transitions(self):
        allowed = ALLOWED_STATUS_TRANSITIONS["Pending"]
        assert "Preparing" in allowed
        assert "Cancelled" in allowed
        assert "Completed" not in allowed

    def test_preparing_transitions(self):
        allowed = ALLOWED_STATUS_TRANSITIONS["Preparing"]
        assert "Ready" in allowed
        assert "Cancelled" in allowed
        assert "Pending" not in allowed

    def test_ready_transitions(self):
        allowed = ALLOWED_STATUS_TRANSITIONS["Ready"]
        assert "Completed" in allowed
        assert "Cancelled" in allowed
        assert "Pending" not in allowed

    def test_completed_is_terminal(self):
        assert len(ALLOWED_STATUS_TRANSITIONS["Completed"]) == 0

    def test_cancelled_is_terminal(self):
        assert len(ALLOWED_STATUS_TRANSITIONS["Cancelled"]) == 0


# ==============================================================================
# 2. Database Integration Tests (Live MySQL Dependent)
# ==============================================================================
@skip_if_no_db
class TestDatabaseOrderOperations:
    def test_create_order_transaction_and_audit(self):
        from services.order_service import create_order
        # Item 1: Masala Chai (15.00), Item 2: Filter Coffee (20.00)
        items = [(1, 2), (2, 1)]  # Total = 2*15 + 1*20 = 50.00
        result = create_order(
            customer_id=1,
            employee_id=2,
            items=items,
            submission_token=f"test-token-{pytest.__name__}-1"
        )
        assert result["order_id"] > 0
        assert result["total_amount"] == 50.00
        assert result["order_status"] == "Pending"
        assert len(result["items"]) == 2

    def test_duplicate_submission_token_rejected(self):
        from services.order_service import create_order
        token = "test-unique-token-999"
        # First creation succeeds
        create_order(customer_id=1, employee_id=2, items=[(1, 1)], submission_token=token)

        # Immediate duplicate submission fails
        with pytest.raises(ValueError, match="Duplicate submission detected"):
            create_order(customer_id=1, employee_id=2, items=[(1, 1)], submission_token=token)

    def test_empty_items_rejected(self):
        from services.order_service import create_order
        with pytest.raises(ValueError, match="at least one item"):
            create_order(customer_id=1, employee_id=2, items=[])

    def test_invalid_status_transition_raises_error(self):
        from services.order_service import create_order, update_status
        order = create_order(customer_id=1, employee_id=2, items=[(1, 1)])
        order_id = order["order_id"]

        # Legal transition: Pending -> Preparing
        res1 = update_status(order_id, "Preparing")
        assert res1["new_status"] == "Preparing"

        # Illegal transition: Preparing -> Completed directly (skipping Ready)
        with pytest.raises(ValueError, match="Illegal transition"):
            update_status(order_id, "Completed")

    def test_payment_recording_and_overpayment_block(self):
        from services.order_service import create_order, record_payment
        # Order total = 1 * 15.00 = 15.00
        order = create_order(customer_id=1, employee_id=2, items=[(1, 1)])
        order_id = order["order_id"]

        # Overpayment should be blocked
        with pytest.raises(ValueError, match="exceeds the order total"):
            record_payment(order_id, "Cash", 50.00)

        # Underpayment should be blocked
        with pytest.raises(ValueError, match="less than order total"):
            record_payment(order_id, "Cash", 10.00)

        # Exact payment succeeds
        payment = record_payment(order_id, "UPI", 15.00)
        assert payment["payment_id"] > 0
        assert payment["payment_status"] == "Paid"

        # Second payment should be rejected (duplicate payment check)
        with pytest.raises(ValueError, match="already has a recorded payment"):
            record_payment(order_id, "Cash", 15.00)

    def test_cannot_pay_for_cancelled_order(self):
        from services.order_service import create_order, update_status, record_payment
        order = create_order(customer_id=1, employee_id=2, items=[(1, 1)])
        order_id = order["order_id"]

        # Cancel the order
        update_status(order_id, "Cancelled")

        # Payment should be blocked
        with pytest.raises(ValueError, match="Cannot record payment for Cancelled order"):
            record_payment(order_id, "Cash", 15.00)
