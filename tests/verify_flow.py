"""
tests/verify_flow.py
====================
Script verifying end-to-end flow:
1. Checks initial dashboard KPI metrics.
2. Creates a new order.
3. Checks dashboard KPI metrics (revenue unchanged, orders count +1, active +1).
4. Advances order status to Completed.
5. Records payment for the order.
6. Checks dashboard KPI metrics (revenue increased, active count decremented).
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.connection import fetch_one
from services.order_service import create_order, update_status, record_payment


def verify_flow():
    q_sales = """
        SELECT COALESCE(SUM(o.total_amount), 0.00) AS sales
        FROM orders o
        INNER JOIN payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'Completed' AND p.payment_status = 'Paid' AND DATE(o.order_datetime) = CURRENT_DATE;
    """

    # 1. Initial State
    s1 = float(fetch_one(q_sales)["sales"])
    o1 = fetch_one("SELECT COUNT(*) AS cnt FROM orders WHERE DATE(order_datetime) = CURRENT_DATE;")["cnt"]
    p1 = fetch_one("SELECT COUNT(*) AS cnt FROM orders WHERE order_status IN ('Pending', 'Preparing', 'Ready');")["cnt"]
    print(f"1. Initial Dashboard: Sales=Rs.{s1:.2f}, Today Orders={o1}, Active Orders={p1}")

    # 2. Create New Order (2x Masala Chai @ 15 = 30, 1x Masala Dosa @ 55 = 55 -> Total = 85.00)
    new_order = create_order(customer_id=1, employee_id=2, items=[(1, 2), (5, 1)])
    oid = new_order["order_id"]
    total = new_order["total_amount"]
    print(f"2. Created Order #{oid} for Rs.{total:.2f} (Status: {new_order['order_status']})")

    # 3. Check State After Creation (Unpaid / Pending)
    s2 = float(fetch_one(q_sales)["sales"])
    o2 = fetch_one("SELECT COUNT(*) AS cnt FROM orders WHERE DATE(order_datetime) = CURRENT_DATE;")["cnt"]
    p2 = fetch_one("SELECT COUNT(*) AS cnt FROM orders WHERE order_status IN ('Pending', 'Preparing', 'Ready');")["cnt"]
    print(f"3. After Order Creation: Sales=Rs.{s2:.2f}, Today Orders={o2}, Active Orders={p2}")

    assert s2 == s1, "Revenue must NOT increase for unpaid/pending order!"
    assert o2 == o1 + 1, "Today orders count must increment by 1!"
    assert p2 == p1 + 1, "Active in-progress orders count must increment by 1!"

    # 4. Advance Status: Pending -> Preparing -> Ready -> Completed
    update_status(oid, "Preparing")
    update_status(oid, "Ready")
    update_status(oid, "Completed")
    print(f"4. Advanced Order #{oid} to 'Completed'.")

    # 5. Record Payment (Rs. 85.00 via UPI)
    payment = record_payment(oid, "UPI", 85.00)
    print(f"5. Recorded Payment #{payment['payment_id']}: Rs.{payment['amount']:.2f} via {payment['payment_method']}")

    # 6. Check State After Payment & Completion
    s3 = float(fetch_one(q_sales)["sales"])
    o3 = fetch_one("SELECT COUNT(*) AS cnt FROM orders WHERE DATE(order_datetime) = CURRENT_DATE;")["cnt"]
    p3 = fetch_one("SELECT COUNT(*) AS cnt FROM orders WHERE order_status IN ('Pending', 'Preparing', 'Ready');")["cnt"]
    print(f"6. After Payment & Completion: Sales=Rs.{s3:.2f}, Today Orders={o3}, Active Orders={p3}")

    assert s3 == s1 + 85.0, "Revenue must increase by exactly the order total!"
    assert p3 == p1, "Active count must return to baseline after order completion!"

    print("\nSUCCESS: All dashboard consistency checks passed with 100% mathematical precision!")


if __name__ == "__main__":
    verify_flow()
