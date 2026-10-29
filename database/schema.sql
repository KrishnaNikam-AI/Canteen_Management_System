-- ==============================================================================
-- CANTEEN MANAGEMENT SYSTEM - DATABASE SCHEMA (MySQL 8.x / MariaDB)
-- ==============================================================================
-- College Viva Concepts:
-- 1. Normalization: Designed in 3NF (Third Normal Form) to eliminate data redundancy.
-- 2. History Protection: ON DELETE RESTRICT prevents accidental deletion of master
--    records (menu items, customers, employees) that are referenced in historical orders.
-- 3. Composite Integrity: ON DELETE CASCADE is applied ONLY to order_items -> orders
--    so that line items are cleaned up if and only if an entire order is purged.
-- 4. Audit Price: order_items stores unit_price at the exact time of ordering,
--    ensuring future menu price changes do not distort historical sales figures.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- OPTIONAL DATABASE RESET SECTION
-- Uncomment the following line ONLY if you want to completely drop the database:
-- DROP DATABASE IF EXISTS canteen_db;
-- ------------------------------------------------------------------------------

-- Step 1: Create Database safely and select it
CREATE DATABASE IF NOT EXISTS canteen_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE canteen_db;

-- ------------------------------------------------------------------------------
-- Drop existing tables in reverse dependency order to ensure clean schema recreation
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS menu_items;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS categories;

-- ------------------------------------------------------------------------------
-- Table 1: categories
-- Master categories for menu organization (Beverages, Snacks, Meals, etc.)
-- ------------------------------------------------------------------------------
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- Table 2: menu_items
-- Food and drink items offered in the canteen
-- Foreign Key: category_id -> categories(category_id) ON DELETE RESTRICT
-- ------------------------------------------------------------------------------
CREATE TABLE menu_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    is_available BOOLEAN NOT NULL DEFAULT 1,
    CONSTRAINT fk_menu_items_category
        FOREIGN KEY (category_id)
        REFERENCES categories(category_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- Table 3: customers
-- Registered students, faculty, and regular campus patrons
-- ------------------------------------------------------------------------------
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(100) NULL UNIQUE
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- Table 4: employees
-- Canteen staff, managers, and cashiers
-- ------------------------------------------------------------------------------
CREATE TABLE employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    phone VARCHAR(15) NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- Table 5: orders
-- Header table for sales transactions.
-- customer_id is NULLABLE to support unregistered walk-in patrons.
-- employee_id is NULLABLE for self-service / kiosk orders.
-- ------------------------------------------------------------------------------
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NULL,
    employee_id INT NULL,
    order_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    order_status ENUM('Pending', 'Preparing', 'Ready', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Pending',
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0),
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_orders_employee
        FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- Table 6: order_items
-- Bridge / line item table resolving Many-to-Many between Orders and Menu Items.
-- Captures unit_price at time of order and calculated subtotal.
-- ------------------------------------------------------------------------------
CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price > 0),
    subtotal DECIMAL(10, 2) NOT NULL CHECK (subtotal >= 0),
    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_order_items_item
        FOREIGN KEY (item_id)
        REFERENCES menu_items(item_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- Table 7: payments
-- Payment record for each order.
-- order_id is UNIQUE (enforces exactly single payment record per order).
-- ------------------------------------------------------------------------------
CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL UNIQUE,
    payment_method ENUM('Cash', 'UPI') NOT NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    payment_status ENUM('Paid', 'Pending', 'Refunded') NOT NULL DEFAULT 'Pending',
    payment_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payments_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- Performance Indexes for Reporting and High-Volume Lookups
-- ------------------------------------------------------------------------------
CREATE INDEX idx_orders_datetime ON orders(order_datetime);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_menu_category ON menu_items(category_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_item ON order_items(item_id);
CREATE INDEX idx_payments_datetime ON payments(payment_datetime);
CREATE INDEX idx_payments_status ON payments(payment_status);
