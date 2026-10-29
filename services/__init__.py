"""
Services Package
Contains core business and reporting logic separated from UI and database layers.
"""

from .order_service import (
    create_order,
    update_status,
    record_payment,
    calculate_order_totals,
    ALLOWED_STATUS_TRANSITIONS,
)
from .report_service import (
    get_daily_sales_report,
    get_popular_menu_items,
    get_order_history,
    get_datewise_sales_summary,
)

__all__ = [
    "create_order",
    "update_status",
    "record_payment",
    "calculate_order_totals",
    "ALLOWED_STATUS_TRANSITIONS",
    "get_daily_sales_report",
    "get_popular_menu_items",
    "get_order_history",
    "get_datewise_sales_summary",
]
