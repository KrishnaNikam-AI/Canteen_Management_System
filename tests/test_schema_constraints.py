"""
tests/test_schema_constraints.py
================================
Validates schema integrity rules:
- FK constraints (RESTRICT on categories, customers; CASCADE on order_items)
- CHECK constraints (price > 0, quantity > 0, total_amount >= 0, amount > 0)
- UNIQUE constraints (category name, customer phone, payment order_id)
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.connection import get_connection, MySQLError, execute, fetch_one


def test_schema_constraints():
    conn = get_connection(include_database=True)
    cursor = conn.cursor()

    print("--- 1. Testing FK RESTRICT on Category Deletion ---")
    # Category 1 has menu items. Deleting it should fail with IntegrityError / MySQLError
    try:
        cursor.execute("DELETE FROM categories WHERE category_id = 1;")
        conn.commit()
        assert False, "Deleting category with active menu items should fail"
    except AssertionError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        print("  [PASS] FK blocked category deletion:", type(exc).__name__)

    print("\n--- 2. Testing FK on Invalid Category Insert ---")
    try:
        cursor.execute("INSERT INTO menu_items (category_id, item_name, price) VALUES (999999, 'Phantom Item', 50.00);")
        conn.commit()
        assert False, "Inserting menu item with invalid category_id should fail"
    except AssertionError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        print("  [PASS] FK blocked orphan menu item:", type(exc).__name__)

    print("\n--- 3. Testing FK RESTRICT on Customer with Orders ---")
    try:
        cursor.execute("DELETE FROM customers WHERE customer_id = 1;")
        conn.commit()
        assert False, "Deleting customer with existing orders should fail"
    except AssertionError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        print("  [PASS] FK blocked customer deletion:", type(exc).__name__)

    print("\n--- 4. Testing CHECK constraint: menu_items.price > 0 ---")
    try:
        cursor.execute("INSERT INTO menu_items (category_id, item_name, price) VALUES (1, 'Negative Item', -10.00);")
        conn.commit()
        assert False, "Negative price should violate CHECK constraint"
    except AssertionError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        print("  [PASS] CHECK constraint blocked negative price:", type(exc).__name__)

    try:
        cursor.execute("INSERT INTO menu_items (category_id, item_name, price) VALUES (1, 'Zero Price Item', 0.00);")
        conn.commit()
        assert False, "Zero price should violate CHECK constraint (price > 0)"
    except AssertionError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        print("  [PASS] CHECK constraint blocked zero price:", type(exc).__name__)

    print("\n--- 5. Testing CHECK constraint: order_items.quantity > 0 ---")
    try:
        cursor.execute("INSERT INTO order_items (order_id, item_id, quantity, unit_price, subtotal) VALUES (1, 1, 0, 15.00, 0.00);")
        conn.commit()
        assert False, "Zero quantity should violate CHECK constraint (quantity > 0)"
    except AssertionError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        print("  [PASS] CHECK constraint blocked zero quantity:", type(exc).__name__)

    print("\n--- 6. Testing CHECK constraint: orders.total_amount >= 0 ---")
    try:
        cursor.execute("INSERT INTO orders (total_amount) VALUES (-50.00);")
        conn.commit()
        assert False, "Negative order total should violate CHECK constraint"
    except AssertionError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        print("  [PASS] CHECK constraint blocked negative order total:", type(exc).__name__)

    print("\n--- 7. Testing UNIQUE constraint on Category Name ---")
    try:
        cursor.execute("INSERT INTO categories (category_name) VALUES ('Beverages');")
        conn.commit()
        assert False, "Duplicate category name should violate UNIQUE constraint"
    except AssertionError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        print("  [PASS] UNIQUE constraint blocked duplicate category name:", type(exc).__name__)

    print("\n--- 8. Testing UNIQUE constraint on Customer Phone ---")
    try:
        # 9811122233 belongs to Aarav Patel in sample_data
        cursor.execute("INSERT INTO customers (customer_name, phone) VALUES ('Clone User', '9811122233');")
        conn.commit()
        assert False, "Duplicate customer phone should violate UNIQUE constraint"
    except AssertionError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        print("  [PASS] UNIQUE constraint blocked duplicate phone:", type(exc).__name__)

    print("\n--- 9. Testing UNIQUE constraint on Payments (1 payment per order) ---")
    try:
        # Order 1 already has a payment
        cursor.execute("INSERT INTO payments (order_id, payment_method, amount, payment_status) VALUES (1, 'Cash', 75.00, 'Paid');")
        conn.commit()
        assert False, "Duplicate payment for same order should violate UNIQUE constraint"
    except AssertionError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        print("  [PASS] UNIQUE constraint blocked duplicate payment record:", type(exc).__name__)

    print("\n--- 10. Testing CASCADE Delete on Order -> Order Items ---")
    # Create a temporary test order with items, then delete the order and verify items are deleted
    cursor.execute("INSERT INTO orders (customer_id, employee_id, order_status, total_amount) VALUES (NULL, 1, 'Cancelled', 50.00);")
    test_order_id = cursor.lastrowid
    cursor.execute("INSERT INTO order_items (order_id, item_id, quantity, unit_price, subtotal) VALUES (%s, 1, 2, 25.00, 50.00);", (test_order_id,))
    conn.commit()

    # Verify item exists
    cursor.execute("SELECT COUNT(*) FROM order_items WHERE order_id = %s;", (test_order_id,))
    assert cursor.fetchone()[0] == 1, "Order item should exist before cascade delete"

    # Delete order
    cursor.execute("DELETE FROM orders WHERE order_id = %s;", (test_order_id,))
    conn.commit()

    # Verify order_items were cascade deleted
    cursor.execute("SELECT COUNT(*) FROM order_items WHERE order_id = %s;", (test_order_id,))
    assert cursor.fetchone()[0] == 0, "Order items should be automatically deleted via CASCADE"
    print(f"  [PASS] ON DELETE CASCADE safely removed items for test order #{test_order_id}")

    cursor.close()
    conn.close()
    print("\nALL 10 SCHEMA CONSTRAINTS AND INTEGRITY RULES VERIFIED SUCCESSFULLY!")


if __name__ == "__main__":
    test_schema_constraints()
