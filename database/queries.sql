-- ==============================================================================
-- CANTEEN MANAGEMENT SYSTEM - ESSENTIAL SQL QUERIES FOR VIVA & REPORTS
-- ==============================================================================
-- This script contains 12 well-documented SQL queries covering:
-- - WHERE & ORDER BY clauses
-- - DISTINCT values
-- - BETWEEN & Date filtering
-- - Aggregate functions (COUNT, SUM, AVG, MIN, MAX)
-- - INNER JOIN and LEFT JOIN
-- - GROUP BY and HAVING clauses
-- - Subqueries (Scalar and correlated)
-- - Multi-table relational queries
-- ==============================================================================

USE canteen_db;

-- ------------------------------------------------------------------------------
-- Query 1: WHERE & ORDER BY
-- Purpose: Retrieve all available menu items priced under ₹60, sorted by price.
-- Viva Concept: WHERE filters rows prior to sorting; ORDER BY arranges results.
-- ------------------------------------------------------------------------------
SELECT 
    item_id,
    item_name,
    price,
    is_available
FROM menu_items
WHERE is_available = 1 AND price <= 60.00
ORDER BY price ASC, item_name ASC;

-- ------------------------------------------------------------------------------
-- Query 2: DISTINCT
-- Purpose: Find all unique customers who have placed at least one completed order.
-- Viva Concept: DISTINCT removes duplicate customer IDs from the projected output.
-- ------------------------------------------------------------------------------
SELECT DISTINCT
    c.customer_id,
    c.customer_name,
    c.phone
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_status = 'Completed'
ORDER BY c.customer_name ASC;

-- ------------------------------------------------------------------------------
-- Query 3: BETWEEN & Date Filtering
-- Purpose: List all orders placed during the mid-month promotional week (Oct 16 to Oct 22).
-- Viva Concept: BETWEEN is inclusive of both boundary timestamps.
-- ------------------------------------------------------------------------------
SELECT 
    order_id,
    order_datetime,
    order_status,
    total_amount
FROM orders
WHERE order_datetime BETWEEN '2026-10-16 00:00:00' AND '2026-10-22 23:59:59'
ORDER BY order_datetime ASC;

-- ------------------------------------------------------------------------------
-- Query 4: Aggregate Functions (COUNT, SUM, AVG, MIN, MAX)
-- Purpose: Executive summary of all completed orders.
-- Viva Concept: Aggregates reduce multiple data rows into summary statistical values.
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(order_id) AS total_completed_orders,
    SUM(total_amount) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS average_order_value,
    MIN(total_amount) AS minimum_bill_amount,
    MAX(total_amount) AS maximum_bill_amount
FROM orders
WHERE order_status = 'Completed';

-- ------------------------------------------------------------------------------
-- Query 5: INNER JOIN
-- Purpose: Display the active menu catalog with corresponding category names.
-- Viva Concept: INNER JOIN requires matching keys in both categories and menu_items.
-- ------------------------------------------------------------------------------
SELECT 
    m.item_id,
    m.item_name,
    c.category_name,
    m.price,
    m.description
FROM menu_items m
INNER JOIN categories c ON m.category_id = c.category_id
WHERE m.is_available = 1
ORDER BY c.category_name ASC, m.price ASC;

-- ------------------------------------------------------------------------------
-- Query 6: LEFT JOIN
-- Purpose: Customer activity report including customers with zero orders.
-- Viva Concept: LEFT JOIN preserves all records from the left table ('customers')
-- and fills unmatched columns from 'orders' with NULL, replaced here via COALESCE.
-- ------------------------------------------------------------------------------
SELECT 
    c.customer_id,
    c.customer_name,
    c.phone,
    COUNT(o.order_id) AS total_orders_placed,
    COALESCE(SUM(CASE WHEN o.order_status = 'Completed' THEN o.total_amount ELSE 0 END), 0.00) AS total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name, c.phone
ORDER BY total_spent DESC;

-- ------------------------------------------------------------------------------
-- Query 7: GROUP BY and HAVING
-- Purpose: Identify food categories generating more than ₹300.00 in total sales.
-- Viva Concept: WHERE filters individual rows before grouping;
-- HAVING filters the aggregated groups after GROUP BY.
-- ------------------------------------------------------------------------------
SELECT 
    c.category_id,
    c.category_name,
    COUNT(oi.order_item_id) AS total_items_sold,
    SUM(oi.subtotal) AS gross_category_sales
FROM categories c
INNER JOIN menu_items m ON c.category_id = m.category_id
INNER JOIN order_items oi ON m.item_id = oi.item_id
INNER JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'Completed'
GROUP BY c.category_id, c.category_name
HAVING gross_category_sales > 300.00
ORDER BY gross_category_sales DESC;

-- ------------------------------------------------------------------------------
-- Query 8: Scalar Subquery
-- Purpose: Find menu items priced strictly higher than the overall average menu item price.
-- Viva Concept: The subquery evaluates once to return a scalar numeric average;
-- the outer query uses that scalar value in its WHERE filter.
-- ------------------------------------------------------------------------------
SELECT 
    item_id,
    item_name,
    price,
    ROUND((SELECT AVG(price) FROM menu_items), 2) AS overall_avg_price
FROM menu_items
WHERE price > (SELECT AVG(price) FROM menu_items)
ORDER BY price DESC;

-- ------------------------------------------------------------------------------
-- Query 9: Subquery with IN
-- Purpose: Find customers who have ordered any dessert items (category_id = 6).
-- Viva Concept: The inner query returns a list of order IDs containing desserts;
-- the outer query finds customers matching those orders.
-- ------------------------------------------------------------------------------
SELECT 
    customer_id,
    customer_name,
    phone
FROM customers
WHERE customer_id IN (
    SELECT DISTINCT o.customer_id
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    INNER JOIN menu_items m ON oi.item_id = m.item_id
    WHERE m.category_id = 6 AND o.customer_id IS NOT NULL
)
ORDER BY customer_name ASC;

-- ------------------------------------------------------------------------------
-- Query 10: Multi-Table Relational Bill / Receipt (Full Order Breakdown)
-- Purpose: Generate a complete itemized bill for Order #2 with customer, cashier, items, and payment.
-- Viva Concept: Comprehensive 6-table relational query joining header, line items, and payment.
-- ------------------------------------------------------------------------------
SELECT 
    o.order_id,
    o.order_datetime,
    COALESCE(c.customer_name, 'Walk-in Customer') AS customer_name,
    e.employee_name AS cashier_name,
    m.item_name,
    oi.quantity,
    oi.unit_price,
    oi.subtotal,
    o.total_amount AS bill_total,
    p.payment_method,
    p.payment_status
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN employees e ON o.employee_id = e.employee_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN menu_items m ON oi.item_id = m.item_id
LEFT JOIN payments p ON o.order_id = p.order_id
WHERE o.order_id = 2;

-- ------------------------------------------------------------------------------
-- Query 11: Payment Breakdown (Cash vs UPI)
-- Purpose: Financial reconciliation breakdown of payments by payment method and status.
-- Viva Concept: Grouping by multiple columns to audit cash handling vs digital payments.
-- ------------------------------------------------------------------------------
SELECT 
    payment_method,
    payment_status,
    COUNT(payment_id) AS transaction_count,
    SUM(amount) AS total_amount
FROM payments
GROUP BY payment_method, payment_status
ORDER BY payment_method ASC, payment_status ASC;

-- ------------------------------------------------------------------------------
-- Query 12: Top 5 Best-Selling Items by Volume
-- Purpose: Identify top 5 menu items by total quantity ordered.
-- Viva Concept: Essential business analytics query combining JOIN, GROUP BY, ORDER BY DESC, and LIMIT.
-- ------------------------------------------------------------------------------
SELECT 
    m.item_id,
    m.item_name,
    c.category_name,
    SUM(oi.quantity) AS total_quantity_sold,
    SUM(oi.subtotal) AS total_revenue_generated
FROM order_items oi
INNER JOIN menu_items m ON oi.item_id = m.item_id
INNER JOIN categories c ON m.category_id = c.category_id
INNER JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'Completed'
GROUP BY m.item_id, m.item_name, c.category_name
ORDER BY total_quantity_sold DESC, total_revenue_generated DESC
LIMIT 5;
