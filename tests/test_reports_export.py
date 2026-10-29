"""
tests/test_reports_export.py
============================
Automated verification for all 4 reports, CSV and PDF generation,
and verifying that no order is counted twice.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.report_service import (
    get_daily_sales_metrics,
    get_daily_sales_report,
    get_popular_menu_items,
    get_order_history,
    get_datewise_sales_summary,
)
from utils.export_utils import export_to_csv, export_to_pdf


def test_reports_and_exports():
    export_dir = ROOT_DIR / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    print("--- 1. Testing Daily Sales Report & Metrics ---")
    metrics = get_daily_sales_metrics()
    daily_rows = get_daily_sales_report()
    print(f"Total Orders: {metrics['total_orders']}")
    print(f"Completed Paid Orders: {metrics['completed_paid_orders']}")
    print(f"Total Revenue: Rs. {metrics['total_revenue']:.2f}")
    print(f"Cash Total: Rs. {metrics['cash_total']:.2f}")
    print(f"UPI Total: Rs. {metrics['upi_total']:.2f}")
    print(f"Itemized completed orders count: {len(daily_rows)}")

    # Check cash + upi == total
    assert round(metrics["cash_total"] + metrics["upi_total"], 2) == round(metrics["total_revenue"], 2), (
        "Cash + UPI does not equal Total Revenue"
    )

    # Check that no completed order is counted twice in daily_rows
    order_ids = [r["order_id"] for r in daily_rows]
    assert len(order_ids) == len(set(order_ids)), "Duplicate order_id detected in daily_sales_report!"
    assert len(order_ids) == metrics["completed_paid_orders"], "Itemized count does not match metric count!"

    # Export Daily Sales CSV and PDF
    daily_headers = ["Order #", "Date & Time", "Customer", "Staff", "Total (Rs)", "Payment Method", "Status", "Items"]
    daily_table_rows = [
        [
            r["order_id"],
            str(r["order_datetime"]),
            r["customer_name"],
            r["employee_name"],
            f"{r['total_amount']:.2f}",
            r["payment_method"],
            r["payment_status"],
            r["items_count"],
        ]
        for r in daily_rows
    ]
    csv_daily = export_to_csv(daily_table_rows, daily_headers, export_dir / "daily_sales_sample.csv")
    pdf_daily = export_to_pdf("Daily Sales Report", daily_table_rows, daily_headers, export_dir / "daily_sales_sample.pdf")
    print(f"  [OK] Daily Sales CSV saved to: {csv_daily}")
    print(f"  [OK] Daily Sales PDF saved to: {pdf_daily}")

    print("\n--- 2. Testing Popular Menu Items ---")
    popular_rows = get_popular_menu_items(limit=10)
    print(f"Popular items retrieved: {len(popular_rows)}")
    popular_headers = ["Item ID", "Item Name", "Category", "Price (Rs)", "Qty Sold", "Sales Total (Rs)"]
    popular_table_rows = [
        [
            r["item_id"],
            r["item_name"],
            r["category_name"],
            f"{r['price']:.2f}",
            r["total_quantity_sold"],
            f"{r['total_revenue']:.2f}",
        ]
        for r in popular_rows
    ]
    csv_pop = export_to_csv(popular_table_rows, popular_headers, export_dir / "popular_items_sample.csv")
    pdf_pop = export_to_pdf("Popular Menu Items", popular_table_rows, popular_headers, export_dir / "popular_items_sample.pdf")
    print(f"  [OK] Popular Items CSV saved to: {csv_pop}")
    print(f"  [OK] Popular Items PDF saved to: {pdf_pop}")

    print("\n--- 3. Testing Order History ---")
    history_rows = get_order_history()
    print(f"Order history rows: {len(history_rows)}")
    history_headers = ["Order #", "Date & Time", "Customer", "Phone", "Staff", "Status", "Total (Rs)", "Method", "Payment"]
    history_table_rows = [
        [
            r["order_id"],
            str(r["order_datetime"]),
            r["customer_name"],
            r["customer_phone"] or "-",
            r["employee_name"],
            r["order_status"],
            f"{r['total_amount']:.2f}",
            r["payment_method"],
            r["payment_status"],
        ]
        for r in history_rows
    ]
    csv_hist = export_to_csv(history_table_rows, history_headers, export_dir / "order_history_sample.csv")
    pdf_hist = export_to_pdf("Order History", history_table_rows, history_headers, export_dir / "order_history_sample.pdf")
    print(f"  [OK] Order History CSV saved to: {csv_hist}")
    print(f"  [OK] Order History PDF saved to: {pdf_hist}")

    print("\n--- 4. Testing Date-wise Sales Summary ---")
    datewise_rows = get_datewise_sales_summary()
    print(f"Date-wise summary records: {len(datewise_rows)}")
    datewise_headers = ["Sales Date", "Total Orders", "Completed", "Cancelled", "Net Revenue (Rs)", "Cash Sales (Rs)", "UPI Sales (Rs)"]
    datewise_table_rows = [
        [
            str(r["sales_date"]),
            r["total_orders_placed"],
            r["completed_orders"],
            r["cancelled_orders"],
            f"{r['net_revenue']:.2f}",
            f"{r['cash_revenue']:.2f}",
            f"{r['upi_revenue']:.2f}",
        ]
        for r in datewise_rows
    ]
    csv_datewise = export_to_csv(datewise_table_rows, datewise_headers, export_dir / "datewise_sales_sample.csv")
    pdf_datewise = export_to_pdf("Date-wise Sales Summary", datewise_table_rows, datewise_headers, export_dir / "datewise_sales_sample.pdf")
    print(f"  [OK] Date-wise Sales CSV saved to: {csv_datewise}")
    print(f"  [OK] Date-wise Sales PDF saved to: {pdf_datewise}")

    print("\n--- 5. Validating File Sizes and Openability ---")
    for filepath in [csv_daily, pdf_daily, csv_pop, pdf_pop, csv_hist, pdf_hist, csv_datewise, pdf_datewise]:
        p = Path(filepath)
        assert p.exists(), f"File does not exist: {p}"
        size = p.stat().st_size
        assert size > 0, f"File is empty: {p}"
        print(f"  Validated {p.name}: {size:,} bytes")

    print("\n==========================================")
    print("ALL 4 REPORTS AND EXPORTS VERIFIED SUCCESSFULLY!")
    print("==========================================")


if __name__ == "__main__":
    test_reports_and_exports()
