"""
web/app.py
==========
Flask Web Application for Canteen Management System.
Reuses db/, services/, and utils/ unchanged from the original project.

All SQL queries live in the same services layer — the web layer only adds
HTTP routing, JSON serialization, and HTML rendering on top.
"""

import sys
import os
import json
from decimal import Decimal
from datetime import date, datetime

# ── Make project root importable ──────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# ── Reuse existing db & service layer (unchanged) ─────────────────────────────
from db.connection import fetch_all, fetch_one, execute, test_connection
from services.order_service import (
    create_order,
    update_status,
    record_payment,
    ALLOWED_STATUS_TRANSITIONS,
)
from services.report_service import (
    get_daily_sales_metrics,
    get_daily_sales_report,
    get_popular_menu_items,
    get_order_history,
    get_datewise_sales_summary,
)
from utils.validators import validate_required, validate_price

# ──────────────────────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.urandom(24)
CORS(app)


# ── JSON encoder that handles Decimal / date types ───────────────────────────
class _Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return str(obj)
        return super().default(obj)

app.json_encoder = _Encoder


def ok(data=None, **kwargs):
    payload = {"success": True}
    if data is not None:
        payload["data"] = data
    payload.update(kwargs)
    return jsonify(payload)


def err(message: str, code: int = 400):
    return jsonify({"success": False, "error": message}), code


# ==============================================================================
# PAGE ROUTES
# ==============================================================================

@app.route("/")
def dashboard():
    return render_template("dashboard.html", active="dashboard")


@app.route("/categories")
def categories():
    return render_template("categories.html", active="categories")


@app.route("/menu")
@app.route("/menu-items")
def menu_items():
    return render_template("menu_items.html", active="menu_items")


@app.route("/customers")
def customers():
    return render_template("customers.html", active="customers")


@app.route("/employees")
def employees():
    return render_template("employees.html", active="employees")


@app.route("/orders")
def orders():
    return render_template("orders.html", active="orders")


@app.route("/payments")
def payments():
    return render_template("payments.html", active="payments")


@app.route("/reports")
def reports():
    return render_template("reports.html", active="reports")


# ==============================================================================
# API — DASHBOARD
# ==============================================================================

@app.route("/api/dashboard/stats")
def api_dashboard_stats():
    try:
        sales = fetch_one("""
            SELECT COALESCE(SUM(o.total_amount), 0) AS today_sales
            FROM orders o INNER JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_status='Completed' AND p.payment_status='Paid'
              AND DATE(o.order_datetime) = CURRENT_DATE;
        """)
        orders_today = fetch_one("SELECT COUNT(*) AS cnt FROM orders WHERE DATE(order_datetime) = CURRENT_DATE;")
        items_avail  = fetch_one("SELECT COUNT(*) AS cnt FROM menu_items WHERE is_available = 1;")
        pending      = fetch_one("SELECT COUNT(*) AS cnt FROM orders WHERE order_status IN ('Pending','Preparing','Ready');")
        recent       = fetch_all("""
            SELECT o.order_id,
                   DATE_FORMAT(o.order_datetime,'%Y-%m-%d %H:%i') AS dt,
                   COALESCE(c.customer_name,'Walk-in') AS customer,
                   o.order_status, o.total_amount,
                   COALESCE(p.payment_status,'Unpaid') AS pay_status
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.customer_id
            LEFT JOIN payments  p ON o.order_id = p.order_id
            ORDER BY o.order_datetime DESC LIMIT 10;
        """)
        chart = fetch_all("""
            SELECT DATE(o.order_datetime) AS day,
                   COALESCE(SUM(p.amount),0) AS revenue
            FROM orders o
            INNER JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_status='Completed' AND p.payment_status='Paid'
              AND o.order_datetime >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
            GROUP BY day ORDER BY day ASC;
        """)
        return ok({
            "today_sales":   float(sales["today_sales"]) if sales else 0,
            "today_orders":  orders_today["cnt"] if orders_today else 0,
            "active_items":  items_avail["cnt"] if items_avail else 0,
            "pending_orders":pending["cnt"] if pending else 0,
            "recent_orders": recent,
            "chart_data":    chart,
        })
    except Exception as e:
        return err(str(e), 500)


# ==============================================================================
# API — CATEGORIES
# ==============================================================================

@app.route("/api/categories")
def api_categories():
    try:
        rows = fetch_all("""
            SELECT c.*, COUNT(m.item_id) AS item_count
            FROM categories c
            LEFT JOIN menu_items m ON c.category_id = m.category_id
            GROUP BY c.category_id ORDER BY c.category_name;
        """)
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/categories", methods=["POST"])
def api_create_category():
    data = request.json or {}
    name = (data.get("category_name") or "").strip()
    desc = (data.get("description") or "").strip()
    errs = validate_required({"Category Name": name})
    if errs:
        return err(errs[0])
    try:
        new_id = execute(
            "INSERT INTO categories (category_name, description) VALUES (%s, %s);",
            (name, desc or None),
        )
        return ok({"category_id": new_id, "category_name": name})
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/categories/<int:cid>", methods=["PUT"])
def api_update_category(cid):
    data = request.json or {}
    name = (data.get("category_name") or "").strip()
    desc = (data.get("description") or "").strip()
    errs = validate_required({"Category Name": name})
    if errs:
        return err(errs[0])
    try:
        execute(
            "UPDATE categories SET category_name=%s, description=%s WHERE category_id=%s;",
            (name, desc or None, cid),
        )
        return ok()
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/categories/<int:cid>", methods=["DELETE"])
def api_delete_category(cid):
    try:
        execute("DELETE FROM categories WHERE category_id=%s;", (cid,))
        return ok()
    except Exception as e:
        return err(str(e), 500)


# ==============================================================================
# API — MENU ITEMS
# ==============================================================================

@app.route("/api/menu-items")
def api_menu_items():
    kw = request.args.get("q", "")
    cat = request.args.get("category_id", "")
    avail = request.args.get("available", "")
    conds, params = [], []
    if kw:
        conds.append("(m.item_name LIKE %s OR c.category_name LIKE %s)")
        params += [f"%{kw}%", f"%{kw}%"]
    if cat:
        conds.append("m.category_id = %s"); params.append(cat)
    if avail in ("0", "1"):
        conds.append("m.is_available = %s"); params.append(int(avail))
    where = "WHERE " + " AND ".join(conds) if conds else ""
    try:
        rows = fetch_all(f"""
            SELECT m.*, c.category_name
            FROM menu_items m
            LEFT JOIN categories c ON m.category_id = c.category_id
            {where} ORDER BY c.category_name, m.item_name;
        """, tuple(params) if params else None)
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/menu-items", methods=["POST"])
def api_create_menu_item():
    data = request.json or {}
    name = (data.get("item_name") or "").strip()
    price_str = str(data.get("price", ""))
    cat_id = data.get("category_id")
    errs = validate_required({"Item Name": name, "Category": cat_id, "Price": price_str})
    if not errs:
        price_errs = validate_price(price_str)
        errs += price_errs
    if errs:
        return err(errs[0])
    try:
        new_id = execute(
            "INSERT INTO menu_items (item_name, category_id, price, description, is_available) VALUES (%s,%s,%s,%s,%s);",
            (name, int(cat_id), float(price_str), data.get("description", ""), int(data.get("is_available", 1))),
        )
        return ok({"item_id": new_id})
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/menu-items/<int:iid>", methods=["PUT"])
def api_update_menu_item(iid):
    data = request.json or {}
    name = (data.get("item_name") or "").strip()
    price_str = str(data.get("price", ""))
    cat_id = data.get("category_id")
    errs = validate_required({"Item Name": name, "Category": cat_id, "Price": price_str})
    if not errs:
        errs += validate_price(price_str)
    if errs:
        return err(errs[0])
    try:
        execute(
            "UPDATE menu_items SET item_name=%s, category_id=%s, price=%s, description=%s, is_available=%s WHERE item_id=%s;",
            (name, int(cat_id), float(price_str), data.get("description", ""), int(data.get("is_available", 1)), iid),
        )
        return ok()
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/menu-items/<int:iid>", methods=["DELETE"])
def api_delete_menu_item(iid):
    try:
        execute("DELETE FROM menu_items WHERE item_id=%s;", (iid,))
        return ok()
    except Exception as e:
        return err(str(e), 500)


# ==============================================================================
# API — CUSTOMERS
# ==============================================================================

@app.route("/api/customers")
def api_customers():
    kw = request.args.get("q", "")
    conds, params = [], []
    if kw:
        conds.append("(customer_name LIKE %s OR phone LIKE %s OR email LIKE %s)")
        params += [f"%{kw}%", f"%{kw}%", f"%{kw}%"]
    where = "WHERE " + " AND ".join(conds) if conds else ""
    try:
        rows = fetch_all(f"SELECT * FROM customers {where} ORDER BY customer_name;",
                         tuple(params) if params else None)
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/customers", methods=["POST"])
def api_create_customer():
    data = request.json or {}
    name = (data.get("customer_name") or "").strip()
    errs = validate_required({"Customer Name": name})
    if errs:
        return err(errs[0])
    try:
        new_id = execute(
            "INSERT INTO customers (customer_name, phone, email, address) VALUES (%s,%s,%s,%s);",
            (name, data.get("phone",""), data.get("email",""), data.get("address","")),
        )
        return ok({"customer_id": new_id})
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/customers/<int:cid>", methods=["PUT"])
def api_update_customer(cid):
    data = request.json or {}
    name = (data.get("customer_name") or "").strip()
    errs = validate_required({"Customer Name": name})
    if errs:
        return err(errs[0])
    try:
        execute(
            "UPDATE customers SET customer_name=%s, phone=%s, email=%s, address=%s WHERE customer_id=%s;",
            (name, data.get("phone",""), data.get("email",""), data.get("address",""), cid),
        )
        return ok()
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/customers/<int:cid>", methods=["DELETE"])
def api_delete_customer(cid):
    try:
        execute("DELETE FROM customers WHERE customer_id=%s;", (cid,))
        return ok()
    except Exception as e:
        return err(str(e), 500)


# ==============================================================================
# API — EMPLOYEES
# ==============================================================================

@app.route("/api/employees")
def api_employees():
    kw = request.args.get("q", "")
    conds, params = [], []
    if kw:
        conds.append("(employee_name LIKE %s OR role LIKE %s OR phone LIKE %s)")
        params += [f"%{kw}%", f"%{kw}%", f"%{kw}%"]
    where = "WHERE " + " AND ".join(conds) if conds else ""
    try:
        rows = fetch_all(f"SELECT * FROM employees {where} ORDER BY employee_name;",
                         tuple(params) if params else None)
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/employees", methods=["POST"])
def api_create_employee():
    data = request.json or {}
    name = (data.get("employee_name") or "").strip()
    errs = validate_required({"Employee Name": name})
    if errs:
        return err(errs[0])
    try:
        new_id = execute(
            "INSERT INTO employees (employee_name, role, phone, email, is_active) VALUES (%s,%s,%s,%s,%s);",
            (name, data.get("role","Staff"), data.get("phone",""), data.get("email",""), 1),
        )
        return ok({"employee_id": new_id})
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/employees/<int:eid>", methods=["PUT"])
def api_update_employee(eid):
    data = request.json or {}
    name = (data.get("employee_name") or "").strip()
    errs = validate_required({"Employee Name": name})
    if errs:
        return err(errs[0])
    try:
        execute(
            "UPDATE employees SET employee_name=%s, role=%s, phone=%s, email=%s, is_active=%s WHERE employee_id=%s;",
            (name, data.get("role","Staff"), data.get("phone",""), data.get("email",""),
             int(data.get("is_active", 1)), eid),
        )
        return ok()
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/employees/<int:eid>", methods=["DELETE"])
def api_delete_employee(eid):
    try:
        execute("DELETE FROM employees WHERE employee_id=%s;", (eid,))
        return ok()
    except Exception as e:
        return err(str(e), 500)


# ==============================================================================
# API — ORDERS
# ==============================================================================

@app.route("/api/orders")
def api_orders():
    kw = request.args.get("q", "")
    status = request.args.get("status", "")
    pay = request.args.get("payment", "")
    conds, params = [], []
    if kw:
        conds.append("(o.order_id=%s OR c.customer_name LIKE %s)")
        params += [kw if kw.isdigit() else 0, f"%{kw}%"]
    if status and status != "All":
        conds.append("o.order_status=%s"); params.append(status)
    if pay and pay != "All":
        if pay == "Unpaid":
            conds.append("p.payment_id IS NULL")
        else:
            conds.append("p.payment_status=%s"); params.append(pay)
    where = "WHERE " + " AND ".join(conds) if conds else ""
    try:
        rows = fetch_all(f"""
            SELECT o.order_id,
                   DATE_FORMAT(o.order_datetime,'%Y-%m-%d %H:%i') AS dt,
                   COALESCE(c.customer_name,'Walk-in') AS customer,
                   COALESCE(e.employee_name,'Self Service') AS employee,
                   o.order_status, o.total_amount,
                   COALESCE(p.payment_method,'-') AS payment_method,
                   COALESCE(p.payment_status,'Unpaid') AS payment_status
            FROM orders o
            LEFT JOIN customers c ON o.customer_id=c.customer_id
            LEFT JOIN employees e ON o.employee_id=e.employee_id
            LEFT JOIN payments  p ON o.order_id=p.order_id
            {where}
            ORDER BY o.order_datetime DESC;
        """, tuple(params) if params else None)
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/orders/<int:oid>/items")
def api_order_items(oid):
    try:
        items = fetch_all("""
            SELECT m.item_name, oi.unit_price, oi.quantity, oi.subtotal
            FROM order_items oi
            INNER JOIN menu_items m ON oi.item_id=m.item_id
            WHERE oi.order_id=%s;
        """, (oid,))
        return ok(items)
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/orders", methods=["POST"])
def api_create_order():
    data = request.json or {}
    customer_id = data.get("customer_id")
    employee_id = data.get("employee_id")
    items = data.get("items", [])   # [{"item_id": x, "quantity": y}, ...]
    if not items:
        return err("Cart is empty. Add items before placing an order.")
    items_tuples = [(int(i["item_id"]), int(i["quantity"])) for i in items]
    try:
        result = create_order(
            customer_id=customer_id,
            employee_id=employee_id,
            items=items_tuples,
            submission_token=f"web-{uuid.uuid4()}",
        )
        return ok(result)
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/orders/<int:oid>/status", methods=["PUT"])
def api_update_order_status(oid):
    data = request.json or {}
    new_status = data.get("status", "")
    try:
        update_status(oid, new_status)
        return ok()
    except Exception as e:
        return err(str(e), 400)


@app.route("/api/orders/dropdown-data")
def api_order_dropdown():
    """Returns customers, employees, and available menu items for the POS form."""
    try:
        custs = fetch_all("SELECT customer_id, customer_name, phone FROM customers ORDER BY customer_name;")
        emps  = fetch_all("SELECT employee_id, employee_name, role FROM employees WHERE is_active=1 ORDER BY employee_name;")
        items = fetch_all("""
            SELECT m.item_id, m.item_name, c.category_name, m.price
            FROM menu_items m INNER JOIN categories c ON m.category_id=c.category_id
            WHERE m.is_available=1 ORDER BY c.category_name, m.item_name;
        """)
        return ok({"customers": custs, "employees": emps, "menu_items": items})
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/orders/allowed-transitions")
def api_allowed_transitions():
    return ok({k: list(v) for k, v in ALLOWED_STATUS_TRANSITIONS.items()})


# ==============================================================================
# API — PAYMENTS
# ==============================================================================

@app.route("/api/payments")
def api_payments():
    kw = request.args.get("q", "")
    method = request.args.get("method", "")
    status = request.args.get("status", "")
    conds, params = [], []
    if kw:
        conds.append("(p.payment_id=%s OR p.order_id=%s OR c.customer_name LIKE %s)")
        params += [kw if kw.isdigit() else 0, kw if kw.isdigit() else 0, f"%{kw}%"]
    if method and method != "All":
        conds.append("p.payment_method=%s"); params.append(method)
    if status and status != "All":
        conds.append("p.payment_status=%s"); params.append(status)
    where = "WHERE " + " AND ".join(conds) if conds else ""
    try:
        rows = fetch_all(f"""
            SELECT p.payment_id, p.order_id,
                   DATE_FORMAT(p.payment_datetime,'%Y-%m-%d %H:%i') AS dt,
                   COALESCE(c.customer_name,'Walk-in') AS customer,
                   p.payment_method, p.amount, p.payment_status
            FROM payments p
            INNER JOIN orders o ON p.order_id=o.order_id
            LEFT JOIN customers c ON o.customer_id=c.customer_id
            {where}
            ORDER BY p.payment_datetime DESC;
        """, tuple(params) if params else None)
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/payments/unpaid-orders")
def api_unpaid_orders():
    try:
        rows = fetch_all("""
            SELECT o.order_id,
                   DATE_FORMAT(o.order_datetime,'%Y-%m-%d %H:%i') AS dt,
                   o.order_status, o.total_amount,
                   COALESCE(c.customer_name,'Walk-in') AS customer
            FROM orders o
            LEFT JOIN payments p ON o.order_id=p.order_id
            LEFT JOIN customers c ON o.customer_id=c.customer_id
            WHERE (p.payment_id IS NULL OR p.payment_status='Pending')
              AND o.order_status != 'Cancelled'
            ORDER BY o.order_id DESC;
        """)
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/payments", methods=["POST"])
def api_record_payment():
    data = request.json or {}
    order_id = data.get("order_id")
    method = data.get("method", "Cash")
    amount = data.get("amount")
    if not order_id:
        return err("Order ID is required.")
    try:
        result = record_payment(order_id=int(order_id), method=method, amount=float(amount))
        return ok(result)
    except Exception as e:
        return err(str(e), 400)


# ==============================================================================
# API — REPORTS
# ==============================================================================

@app.route("/api/reports/daily")
def api_report_daily():
    from_d = request.args.get("from") or None
    to_d   = request.args.get("to") or None
    try:
        metrics = get_daily_sales_metrics(from_d, to_d)
        rows    = get_daily_sales_report(from_d, to_d)
        return ok({"metrics": metrics, "rows": rows})
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/reports/popular")
def api_report_popular():
    from_d = request.args.get("from") or None
    to_d   = request.args.get("to") or None
    limit  = int(request.args.get("limit", 10))
    try:
        rows = get_popular_menu_items(from_d, to_d, limit)
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/reports/history")
def api_report_history():
    from_d  = request.args.get("from") or None
    to_d    = request.args.get("to") or None
    status  = request.args.get("status") or None
    try:
        rows = get_order_history(from_d, to_d, status)
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/reports/datewise")
def api_report_datewise():
    from_d = request.args.get("from") or None
    to_d   = request.args.get("to") or None
    try:
        rows = get_datewise_sales_summary(from_d, to_d)
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)


# ==============================================================================
if __name__ == "__main__":
    ok_db, msg = test_connection()
    print(f"Database: {'✅ Connected' if ok_db else '❌ ' + msg}")
    app.run(debug=True, host="0.0.0.0", port=5000)
