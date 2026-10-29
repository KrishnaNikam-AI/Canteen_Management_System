"""
services/order_service.py
=========================
Core Business Logic for Order Processing, Status Lifecycle, and Payments.

College Viva Concepts:
1. ACID Transactions (Atomicity): In create_order(), inserting the order header,
   verifying menu item availability/prices, and creating line items occur within
   a single atomic transaction. Any error rolls back all modifications completely.
2. Status Lifecycle State Machine: Orders must transition strictly along valid paths:
   Pending -> Preparing -> Ready -> Completed (or Cancelled at any open stage).
   Terminal states ('Completed', 'Cancelled') are immutable.
3. Payment Integrity: Payments are restricted to Cash or UPI, cannot exceed or underpay
   the bill, cannot be duplicated (1:1 constraint), and cannot be recorded on cancelled orders.
4. Sales Accounting Rule: Cancelled orders NEVER count towards sales revenue.
"""

from decimal import Decimal
import time
from typing import List, Tuple, Dict, Any, Optional
from db.connection import get_db_cursor, fetch_one, execute

# Set to track processed submission tokens for idempotency / duplicate prevention
_PROCESSED_SUBMISSION_TOKENS = set()

# State transition matrix for order lifecycle
ALLOWED_STATUS_TRANSITIONS = {
    "Pending": {"Preparing", "Cancelled"},
    "Preparing": {"Ready", "Cancelled"},
    "Ready": {"Completed", "Cancelled"},
    "Completed": set(),  # Terminal state
    "Cancelled": set(),  # Terminal state
}


def calculate_order_totals(
    items: List[Dict[str, Any]], discount_percent: float = 0.0
) -> Tuple[float, float, float]:
    """
    Pure utility function to calculate gross total, discount, and final amount.
    Does not require database access (ideal for UI previews and unit tests).

    Args:
        items: List of dicts, each with 'price' and 'quantity'.
        discount_percent: Optional percentage discount (0 to 100).

    Returns:
        Tuple[float, float, float]: (gross_total, discount_amount, final_amount)
    """
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount percentage must be between 0 and 100.")

    gross_total = Decimal("0.00")
    for item in items:
        price = Decimal(str(item.get("price", 0)))
        qty = int(item.get("quantity", 0))
        if price < 0 or qty < 0:
            raise ValueError("Price and quantity must be non-negative.")
        gross_total += price * qty

    discount_amount = (gross_total * Decimal(str(discount_percent))) / Decimal("100.00")
    discount_amount = round(discount_amount, 2)
    final_amount = round(max(Decimal("0.00"), gross_total - discount_amount), 2)

    return float(gross_total), float(discount_amount), float(final_amount)


def create_order(
    customer_id: Optional[int],
    employee_id: Optional[int],
    items: List[Tuple[int, int]],
    submission_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates an order and its line items inside a single ACID MySQL transaction.

    Steps executed inside transaction:
    1. Validate non-empty cart, valid quantities, and check idempotency token.
    2. Read current price and availability of each item from menu_items.
    3. Calculate item subtotals and overall order total.
    4. Insert into 'orders' table (default status 'Pending').
    5. Insert line items into 'order_items' table with unit_price audit snapshot.
    6. Commit transaction and return order summary. If any error occurs, rolls back.

    Args:
        customer_id: ID of registered customer, or None for walk-in patron.
        employee_id: ID of employee/cashier handling order, or None.
        items: List of (item_id, quantity) tuples.
        submission_token: Optional unique client token to prevent duplicate submissions.

    Returns:
        Dict[str, Any]: Created order details (order_id, total_amount, items, status).

    Raises:
        ValueError: On empty cart, unavailable item, invalid quantity, or duplicate token.
        Exception: On database connection or execution failure (triggers rollback).
    """
    # 1. Validation & Duplicate Prevention
    if submission_token:
        if submission_token in _PROCESSED_SUBMISSION_TOKENS:
            raise ValueError(f"Duplicate submission detected. Token '{submission_token}' has already been processed.")
        _PROCESSED_SUBMISSION_TOKENS.add(submission_token)

    if not items:
        raise ValueError("Cannot create an empty order. Cart must contain at least one item.")

    # Validate quantities
    cleaned_items: List[Tuple[int, int]] = []
    for item_id, qty in items:
        try:
            int_qty = int(qty)
            int_item_id = int(item_id)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid item ID or quantity: item_id={item_id}, quantity={qty}")

        if int_qty <= 0:
            raise ValueError(f"Quantity for item ID {int_item_id} must be strictly greater than 0.")
        cleaned_items.append((int_item_id, int_qty))

    # 2. Transaction Execution
    with get_db_cursor(commit=True) as (_, cursor):
        total_amount = Decimal("0.00")
        line_items_data = []

        # Read prices and availability from menu_items
        for item_id, qty in cleaned_items:
            cursor.execute(
                "SELECT item_id, item_name, price, is_available FROM menu_items WHERE item_id = %s FOR UPDATE;",
                (item_id,),
            )
            item_row = cursor.fetchone()
            if not item_row:
                raise ValueError(f"Menu item ID {item_id} does not exist in the database.")

            if not item_row["is_available"]:
                raise ValueError(f"Item '{item_row['item_name']}' is currently marked unavailable.")

            unit_price = Decimal(str(item_row["price"]))
            subtotal = unit_price * qty
            total_amount += subtotal

            line_items_data.append({
                "item_id": item_id,
                "item_name": item_row["item_name"],
                "quantity": qty,
                "unit_price": unit_price,
                "subtotal": subtotal,
            })

        # Insert Order Header
        cursor.execute(
            """
            INSERT INTO orders (customer_id, employee_id, order_datetime, order_status, total_amount)
            VALUES (%s, %s, NOW(), 'Pending', %s);
            """,
            (customer_id, employee_id, total_amount),
        )
        order_id = cursor.lastrowid

        # Insert Order Line Items
        for line in line_items_data:
            cursor.execute(
                """
                INSERT INTO order_items (order_id, item_id, quantity, unit_price, subtotal)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (order_id, line["item_id"], line["quantity"], line["unit_price"], line["subtotal"]),
            )

        return {
            "order_id": order_id,
            "customer_id": customer_id,
            "employee_id": employee_id,
            "order_status": "Pending",
            "total_amount": float(total_amount),
            "items_count": len(line_items_data),
            "items": line_items_data,
        }


def update_status(order_id: int, new_status: str) -> Dict[str, Any]:
    """
    Transitions an order to a new status according to state machine rules:
    - Pending -> Preparing or Cancelled
    - Preparing -> Ready or Cancelled
    - Ready -> Completed or Cancelled
    - Completed / Cancelled are terminal (cannot be changed)

    Args:
        order_id: Target order ID.
        new_status: Next status to set.

    Returns:
        Dict[str, Any]: Updated order info.

    Raises:
        ValueError: If order does not exist or transition is illegal.
    """
    valid_statuses = {"Pending", "Preparing", "Ready", "Completed", "Cancelled"}
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status '{new_status}'. Allowed statuses: {sorted(valid_statuses)}")

    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute("SELECT order_id, order_status FROM orders WHERE order_id = %s FOR UPDATE;", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise ValueError(f"Order #{order_id} does not exist.")

        current_status = order["order_status"]

        if current_status == new_status:
            return {"order_id": order_id, "status": current_status, "message": "Status unchanged."}

        allowed = ALLOWED_STATUS_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            if not allowed:
                raise ValueError(
                    f"Order #{order_id} is in terminal status '{current_status}' and cannot be updated."
                )
            raise ValueError(
                f"Illegal transition: Cannot change Order #{order_id} from '{current_status}' to '{new_status}'. "
                f"Allowed transitions from '{current_status}' are: {sorted(allowed)}."
            )

        cursor.execute("UPDATE orders SET order_status = %s WHERE order_id = %s;", (new_status, order_id))

        return {
            "order_id": order_id,
            "previous_status": current_status,
            "new_status": new_status,
        }


def record_payment(order_id: int, method: str, amount: Any) -> Dict[str, Any]:
    """
    Records a payment for an order.
    Enforces business rules:
    - Payment method must be 'Cash' or 'UPI' (UPI is a recorded method, never asks for PINs).
    - Prevents duplicate payments for the same order (1:1 constraint).
    - Prevents payment above the order total amount.
    - Prevents underpayment (must match order total).
    - Blocks payment on Cancelled orders.

    Args:
        order_id: Target order ID.
        method: Payment method ('Cash' or 'UPI').
        amount: Payment amount.

    Returns:
        Dict[str, Any]: Recorded payment details.

    Raises:
        ValueError: If order is cancelled, payment is duplicate, or amount is invalid.
    """
    if method not in ("Cash", "UPI"):
        raise ValueError("Payment method must be either 'Cash' or 'UPI'.")

    try:
        amt = Decimal(str(amount))
        if amt <= Decimal("0.00"):
            raise ValueError()
    except Exception:
        raise ValueError("Payment amount must be a valid positive number greater than 0.")

    with get_db_cursor(commit=True) as (_, cursor):
        # 1. Fetch order
        cursor.execute("SELECT order_id, order_status, total_amount FROM orders WHERE order_id = %s FOR UPDATE;", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise ValueError(f"Order #{order_id} does not exist.")

        # 2. Block payment on Cancelled orders
        if order["order_status"] == "Cancelled":
            raise ValueError(f"Cannot record payment for Cancelled order #{order_id}.")

        order_total = Decimal(str(order["total_amount"]))

        # 3. Prevent overpayment or underpayment
        if amt > order_total:
            raise ValueError(f"Payment amount (₹{amt:.2f}) exceeds the order total (₹{order_total:.2f}).")
        if amt < order_total:
            raise ValueError(f"Payment amount (₹{amt:.2f}) is less than order total (₹{order_total:.2f}). Partial payments are not allowed.")

        # 4. Check for duplicate payment
        cursor.execute("SELECT payment_id, payment_status FROM payments WHERE order_id = %s;", (order_id,))
        existing_payment = cursor.fetchone()
        if existing_payment:
            raise ValueError(
                f"Order #{order_id} already has a recorded payment (Payment ID #{existing_payment['payment_id']}). "
                f"Duplicate payments are prohibited."
            )

        # 5. Insert payment record
        cursor.execute(
            """
            INSERT INTO payments (order_id, payment_method, amount, payment_status, payment_datetime)
            VALUES (%s, %s, %s, 'Paid', NOW());
            """,
            (order_id, method, amt),
        )
        payment_id = cursor.lastrowid

        return {
            "payment_id": payment_id,
            "order_id": order_id,
            "payment_method": method,
            "amount": float(amt),
            "payment_status": "Paid",
        }
