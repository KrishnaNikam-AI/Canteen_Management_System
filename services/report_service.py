"""
services/report_service.py
==========================
Reporting and Business Analytics Service for Canteen Management System.

================================================================================
REVENUE ACCOUNTING RULE (College Viva Concept):
Revenue is strictly defined as the sum of orders with status = 'Completed'
AND a corresponding payment record with payment_status = 'Paid'.
Cancelled, pending, and refunded orders are rigorously excluded from revenue
totals. Furthermore, each completed order is counted exactly once to eliminate
double-counting across multiple line items.
================================================================================
"""

from typing import List, Dict, Any, Optional
from db.connection import fetch_all, fetch_one


def get_daily_sales_metrics(
    start_date: Optional[str] = None, end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes summary metrics for the Daily Sales Report:
    - Total order count
    - Completed paid order count
    - Total completed paid sales revenue
    - Payment totals by Cash and UPI
    """
    query = """
        SELECT 
            COUNT(DISTINCT o.order_id) AS total_orders,
            COUNT(DISTINCT CASE WHEN o.order_status = 'Completed' AND p.payment_status = 'Paid' THEN o.order_id END) AS completed_paid_orders,
            COALESCE(SUM(CASE WHEN o.order_status = 'Completed' AND p.payment_status = 'Paid' THEN o.total_amount END), 0.00) AS total_revenue,
            COALESCE(SUM(CASE WHEN o.order_status = 'Completed' AND p.payment_status = 'Paid' AND p.payment_method = 'Cash' THEN o.total_amount END), 0.00) AS cash_total,
            COALESCE(SUM(CASE WHEN o.order_status = 'Completed' AND p.payment_status = 'Paid' AND p.payment_method = 'UPI' THEN o.total_amount END), 0.00) AS upi_total
        FROM orders o
        LEFT JOIN payments p ON o.order_id = p.order_id
        WHERE (%s IS NULL OR DATE(o.order_datetime) >= %s)
          AND (%s IS NULL OR DATE(o.order_datetime) <= %s);
    """
    res = fetch_one(query, (start_date, start_date, end_date, end_date))
    if not res:
        return {
            "total_orders": 0,
            "completed_paid_orders": 0,
            "total_revenue": 0.00,
            "cash_total": 0.00,
            "upi_total": 0.00,
        }
    return {
        "total_orders": res["total_orders"] or 0,
        "completed_paid_orders": res["completed_paid_orders"] or 0,
        "total_revenue": float(res["total_revenue"] or 0.00),
        "cash_total": float(res["cash_total"] or 0.00),
        "upi_total": float(res["upi_total"] or 0.00),
    }


def get_daily_sales_report(
    start_date: Optional[str] = None, end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Returns an itemized list of all paid, completed orders for a date or date range.
    """
    query = """
        SELECT 
            o.order_id,
            DATE_FORMAT(o.order_datetime, '%Y-%m-%d %H:%i') AS order_datetime,
            COALESCE(c.customer_name, 'Walk-in Customer') AS customer_name,
            COALESCE(e.employee_name, 'Self Service') AS employee_name,
            o.total_amount,
            p.payment_method,
            p.payment_status,
            COUNT(oi.order_item_id) AS items_count
        FROM orders o
        INNER JOIN payments p ON o.order_id = p.order_id
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN employees e ON o.employee_id = e.employee_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'Completed'
          AND p.payment_status = 'Paid'
          AND (%s IS NULL OR DATE(o.order_datetime) >= %s)
          AND (%s IS NULL OR DATE(o.order_datetime) <= %s)
        GROUP BY o.order_id, o.order_datetime, c.customer_name, e.employee_name, o.total_amount, p.payment_method, p.payment_status
        ORDER BY o.order_datetime DESC;
    """
    return fetch_all(query, (start_date, start_date, end_date, end_date))


def get_popular_menu_items(
    start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 15
) -> List[Dict[str, Any]]:
    """
    Returns top-selling menu items ranked by total quantity sold.
    Only includes items from 'Completed' orders with 'Paid' payments.
    """
    query = """
        SELECT 
            m.item_id,
            m.item_name,
            c.category_name,
            m.price,
            COALESCE(SUM(oi.quantity), 0) AS total_quantity_sold,
            COALESCE(SUM(oi.subtotal), 0.00) AS total_revenue
        FROM menu_items m
        INNER JOIN categories c ON m.category_id = c.category_id
        INNER JOIN order_items oi ON m.item_id = oi.item_id
        INNER JOIN orders o ON oi.order_id = o.order_id
        INNER JOIN payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'Completed'
          AND p.payment_status = 'Paid'
          AND (%s IS NULL OR DATE(o.order_datetime) >= %s)
          AND (%s IS NULL OR DATE(o.order_datetime) <= %s)
        GROUP BY m.item_id, m.item_name, c.category_name, m.price
        ORDER BY total_quantity_sold DESC, total_revenue DESC
        LIMIT %s;
    """
    return fetch_all(query, (start_date, start_date, end_date, end_date, limit))


def get_order_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Fetches chronological order history with flexible filters.
    """
    query = """
        SELECT 
            o.order_id,
            DATE_FORMAT(o.order_datetime, '%Y-%m-%d %H:%i') AS order_datetime,
            COALESCE(c.customer_name, 'Walk-in') AS customer_name,
            c.phone AS customer_phone,
            COALESCE(e.employee_name, 'Self Service') AS employee_name,
            o.order_status,
            o.total_amount,
            COALESCE(p.payment_method, 'None') AS payment_method,
            COALESCE(p.payment_status, 'Unpaid') AS payment_status
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN employees e ON o.employee_id = e.employee_id
        LEFT JOIN payments p ON o.order_id = p.order_id
        WHERE (%s IS NULL OR DATE(o.order_datetime) >= %s)
          AND (%s IS NULL OR DATE(o.order_datetime) <= %s)
          AND (%s IS NULL OR o.order_status = %s)
          AND (%s IS NULL OR o.customer_id = %s)
        ORDER BY o.order_datetime DESC;
    """
    return fetch_all(
        query,
        (start_date, start_date, end_date, end_date, status, status, customer_id, customer_id),
    )


def get_datewise_sales_summary(
    start_date: Optional[str] = None, end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generates a daily summary of sales performance.
    Adheres strictly to the Revenue Rule: Only 'Completed' orders with 'Paid'
    payments are counted towards net_revenue, cash_revenue, and upi_revenue.
    """
    query = """
        SELECT 
            DATE_FORMAT(o.order_datetime, '%Y-%m-%d') AS sales_date,
            COUNT(DISTINCT o.order_id) AS total_orders_placed,
            COUNT(DISTINCT CASE WHEN o.order_status = 'Completed' THEN o.order_id END) AS completed_orders,
            COUNT(DISTINCT CASE WHEN o.order_status = 'Cancelled' THEN o.order_id END) AS cancelled_orders,
            COALESCE(SUM(CASE WHEN o.order_status = 'Completed' AND p.payment_status = 'Paid' THEN o.total_amount ELSE 0 END), 0.00) AS net_revenue,
            COALESCE(SUM(CASE WHEN o.order_status = 'Completed' AND p.payment_status = 'Paid' AND p.payment_method = 'Cash' THEN o.total_amount ELSE 0 END), 0.00) AS cash_revenue,
            COALESCE(SUM(CASE WHEN o.order_status = 'Completed' AND p.payment_status = 'Paid' AND p.payment_method = 'UPI' THEN o.total_amount ELSE 0 END), 0.00) AS upi_revenue
        FROM orders o
        LEFT JOIN payments p ON o.order_id = p.order_id
        WHERE (%s IS NULL OR DATE(o.order_datetime) >= %s)
          AND (%s IS NULL OR DATE(o.order_datetime) <= %s)
        GROUP BY DATE_FORMAT(o.order_datetime, '%Y-%m-%d')
        ORDER BY sales_date DESC;
    """
    return fetch_all(query, (start_date, start_date, end_date, end_date))
