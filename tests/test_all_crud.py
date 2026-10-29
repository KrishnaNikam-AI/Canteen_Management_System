"""
tests/test_all_crud.py
======================
Comprehensive CRUD, Validation, Transaction Rollback, and FK Protection Verification
for all modules: Categories, Menu Items, Customers, Employees, Orders, and Payments.
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.connection import get_connection, execute, fetch_one, fetch_all, MySQLError
from utils.validators import (
    validate_required,
    validate_price,
    validate_quantity,
    validate_phone,
    validate_email,
    validate_name,
)
from services.order_service import (
    create_order,
    update_status,
    record_payment,
    ALLOWED_STATUS_TRANSITIONS,
)


# ==============================================================================
# 1. CATEGORIES CRUD & FK PROTECTION
# ==============================================================================
def test_categories_crud_and_fk_protection():
    # 1. Add Category
    cat_name = "Automated Test Category"
    execute("INSERT INTO categories (category_name, description) VALUES (%s, %s);", (cat_name, "Temp desc"))
    created = fetch_one("SELECT * FROM categories WHERE category_name = %s;", (cat_name,))
    assert created is not None, "Category should be inserted"
    cat_id = created["category_id"]

    # 2. Prevent Duplicate Name
    with pytest.raises(Exception):
        execute("INSERT INTO categories (category_name) VALUES (%s);", (cat_name,))

    # 3. Update Category
    execute("UPDATE categories SET description = %s WHERE category_id = %s;", ("Updated desc", cat_id))
    updated = fetch_one("SELECT * FROM categories WHERE category_id = %s;", (cat_id,))
    assert updated["description"] == "Updated desc"

    # 4. Attach a Menu Item to test FK Protection
    execute(
        "INSERT INTO menu_items (category_id, item_name, price) VALUES (%s, %s, %s);",
        (cat_id, "Test Food Item", 40.00),
    )
    food = fetch_one("SELECT * FROM menu_items WHERE item_name = %s;", ("Test Food Item",))
    food_id = food["item_id"]

    # Deleting category now MUST be blocked by FK
    with pytest.raises(Exception):
        execute("DELETE FROM categories WHERE category_id = %s;", (cat_id,))

    # Remove attached menu item
    execute("DELETE FROM menu_items WHERE item_id = %s;", (food_id,))

    # Now deletion of category without menu items MUST succeed
    execute("DELETE FROM categories WHERE category_id = %s;", (cat_id,))
    deleted = fetch_one("SELECT * FROM categories WHERE category_id = %s;", (cat_id,))
    assert deleted is None, "Category without items should be deleted cleanly"


# ==============================================================================
# 2. MENU ITEMS CRUD & FK PROTECTION
# ==============================================================================
def test_menu_items_crud_and_fk_protection():
    # 1. Validation checks
    assert validate_price(-5.0)[0] is False, "Negative price must be invalid"
    assert validate_price(0.0)[0] is False, "Zero price must be invalid"
    assert validate_price(50.0)[0] is True, "Positive price must be valid"

    # 2. Add Menu Item
    item_name = "CRUD Test Roll"
    execute(
        "INSERT INTO menu_items (category_id, item_name, description, price, is_available) VALUES (%s, %s, %s, %s, %s);",
        (1, item_name, "Tasty roll", 65.00, 1),
    )
    item = fetch_one("SELECT * FROM menu_items WHERE item_name = %s;", (item_name,))
    assert item is not None
    item_id = item["item_id"]

    # 3. Update Menu Item
    execute("UPDATE menu_items SET price = %s WHERE item_id = %s;", (70.00, item_id))
    updated = fetch_one("SELECT * FROM menu_items WHERE item_id = %s;", (item_id,))
    assert float(updated["price"]) == 70.00

    # 4. Toggle Availability
    execute("UPDATE menu_items SET is_available = %s WHERE item_id = %s;", (0, item_id))
    toggled = fetch_one("SELECT is_available FROM menu_items WHERE item_id = %s;", (item_id,))
    assert toggled["is_available"] == 0

    # 5. FK Protection: Menu Item used in Orders cannot be deleted
    # Masala Chai (item_id 1) is used in sample orders 1, 2, etc.
    with pytest.raises(Exception):
        execute("DELETE FROM menu_items WHERE item_id = 1;")

    # 6. Unused Menu Item can be deleted
    execute("DELETE FROM menu_items WHERE item_id = %s;", (item_id,))
    assert fetch_one("SELECT * FROM menu_items WHERE item_id = %s;", (item_id,)) is None


# ==============================================================================
# 3. CUSTOMERS CRUD & FK PROTECTION
# ==============================================================================
def test_customers_crud_and_fk_protection():
    # 1. Validation checks
    assert validate_phone("123")[0] is False, "Short phone must be rejected"
    assert validate_phone("9812345678")[0] is True, "10-digit Indian phone must pass"
    assert validate_email("invalid-email")[0] is False, "Invalid email must fail"
    assert validate_email("test@college.edu")[0] is True, "Valid email must pass"

    # 2. Add Customer
    c_phone = "9712398765"
    execute(
        "INSERT INTO customers (customer_name, phone, email) VALUES (%s, %s, %s);",
        ("CRUD Test Customer", c_phone, "crud.test@college.edu"),
    )
    cust = fetch_one("SELECT * FROM customers WHERE phone = %s;", (c_phone,))
    assert cust is not None
    cust_id = cust["customer_id"]

    # 3. Duplicate Phone blocked
    with pytest.raises(Exception):
        execute("INSERT INTO customers (customer_name, phone) VALUES (%s, %s);", ("Clone", c_phone))

    # 4. Update Customer
    execute("UPDATE customers SET customer_name = %s WHERE customer_id = %s;", ("Updated Customer Name", cust_id))
    assert fetch_one("SELECT customer_name FROM customers WHERE customer_id = %s;", (cust_id,))["customer_name"] == "Updated Customer Name"

    # 5. FK Protection: Customer with Orders cannot be deleted
    # Customer 1 (Aarav Patel) has existing orders
    with pytest.raises(Exception):
        execute("DELETE FROM customers WHERE customer_id = 1;")

    # 6. Unused Customer can be deleted
    execute("DELETE FROM customers WHERE customer_id = %s;", (cust_id,))
    assert fetch_one("SELECT * FROM customers WHERE customer_id = %s;", (cust_id,)) is None


# ==============================================================================
# 4. EMPLOYEES CRUD
# ==============================================================================
def test_employees_crud():
    # 1. Add Employee
    emp_name = "CRUD Staff Member"
    execute(
        "INSERT INTO employees (employee_name, role, phone, is_active) VALUES (%s, %s, %s, %s);",
        (emp_name, "Cashier", "9123491234", 1),
    )
    emp = fetch_one("SELECT * FROM employees WHERE employee_name = %s;", (emp_name,))
    assert emp is not None
    emp_id = emp["employee_id"]

    # 2. Update Employee
    execute("UPDATE employees SET role = %s WHERE employee_id = %s;", ("Manager", emp_id))
    assert fetch_one("SELECT role FROM employees WHERE employee_id = %s;", (emp_id,))["role"] == "Manager"

    # 3. Toggle Active Status
    execute("UPDATE employees SET is_active = %s WHERE employee_id = %s;", (0, emp_id))
    assert fetch_one("SELECT is_active FROM employees WHERE employee_id = %s;", (emp_id,))["is_active"] == 0

    # Clean up test employee
    execute("DELETE FROM employees WHERE employee_id = %s;", (emp_id,))


# ==============================================================================
# 5. ORDERS TRANSACTION ROLLBACK & TOTAL CALCULATION
# ==============================================================================
def test_order_transaction_rollback_on_failure():
    initial_orders_count = fetch_one("SELECT COUNT(*) AS c FROM orders;")["c"]

    # Attempt to create order with an unavailable / invalid item (e.g. item_id 999999)
    try:
        create_order(
            customer_id=1,
            employee_id=1,
            items=[(1, 2), (999999, 1)],  # 999999 does not exist
        )
        assert False, "Order with non-existent item should fail"
    except ValueError:
        pass  # Expected rejection

    final_orders_count = fetch_one("SELECT COUNT(*) AS c FROM orders;")["c"]
    assert initial_orders_count == final_orders_count, "Transaction rollback failed! Order count increased on error."


# ==============================================================================
# 6. COMPLETE POS FLOW: ORDER CREATION -> STATUS MACHINE -> PAYMENT
# ==============================================================================
def test_complete_pos_flow_and_payment_guards():
    # 1. Create Order: 2 Masala Chai (2 * 15.00 = 30.00)
    order = create_order(customer_id=None, employee_id=1, items=[(1, 2)])
    order_id = order["order_id"]
    assert order["total_amount"] == 30.00
    assert order["order_status"] == "Pending"

    # 2. Status Transition: Pending -> Preparing -> Ready -> Completed
    update_status(order_id, "Preparing")
    update_status(order_id, "Ready")
    update_status(order_id, "Completed")

    # Cannot transition from Completed (terminal state)
    with pytest.raises(ValueError, match="terminal"):
        update_status(order_id, "Cancelled")

    # 3. Payment Guard: Overpayment blocked
    with pytest.raises(ValueError, match="exceeds the order total"):
        record_payment(order_id, "Cash", 50.00)

    # 4. Payment Guard: Underpayment blocked
    with pytest.raises(ValueError, match="less than order total"):
        record_payment(order_id, "Cash", 20.00)

    # 5. Payment: Exact payment succeeds
    pay_res = record_payment(order_id, "Cash", 30.00)
    assert pay_res["payment_status"] == "Paid"

    # 6. Duplicate Payment Guard: Second payment blocked
    with pytest.raises(ValueError, match="already has a recorded payment"):
        record_payment(order_id, "UPI", 30.00)


if __name__ == "__main__":
    test_categories_crud_and_fk_protection()
    print("[PASS] Categories CRUD & FK protection")
    test_menu_items_crud_and_fk_protection()
    print("[PASS] Menu Items CRUD & FK protection")
    test_customers_crud_and_fk_protection()
    print("[PASS] Customers CRUD & FK protection")
    test_employees_crud()
    print("[PASS] Employees CRUD")
    test_order_transaction_rollback_on_failure()
    print("[PASS] Order transaction rollback on failure")
    test_complete_pos_flow_and_payment_guards()
    print("[PASS] Complete POS flow, status transitions, and payment guards")
    print("\nALL MODULE CRUD, TRANSACTIONS, AND RULES PASSED!")
