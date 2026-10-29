# Canteen Management System (Web Application)

A modern full-stack web application for college canteen management built with **Python (Flask)**, **HTML5/CSS3/JavaScript**, and **MySQL/MariaDB**. Features real-time master-data management, Point-of-Sale (POS) order processing, cashier payment auditing, interactive analytical reporting with Chart.js, and PDF export capabilities.

---

## 📋 System Requirements

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** Python 3.10 or higher
- **Database:** MySQL 8.0+ or MariaDB (via XAMPP)
- **Browser:** Any modern browser (Chrome, Edge, Firefox, Brave, Safari)

---

## 🚀 Quick Start Guide

### Step 1: Install Python
1. Download Python 3.10+ from [python.org](https://www.python.org/).
2. **Important:** During installation, check the box **"Add python.exe to PATH"**.

### Step 2: Install and Start MySQL (via XAMPP)
1. Download and install [XAMPP](https://www.apachefriends.org/).
2. Open the **XAMPP Control Panel**.
3. Click the **Start** button next to **MySQL** (ensure it shows running on port **3306**).

### Step 3: Configure Environment Variables (`.env`)
1. In the project root directory, copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```
2. Open `.env` in Notepad and verify database credentials:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=canteen_db
   ```
   > **Note for XAMPP users:** The default user is `root` with an **empty** password (`DB_PASSWORD=`).

### Step 4: Install Python Dependencies
Open your terminal in the project folder and install the required packages:
```bash
pip install -r requirements.txt
```

*(Optional: Use a Python virtual environment)*
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 5: Initialize the Database
Execute the database setup script to create `canteen_db`, build all 7 normalized relational tables, and load sample records:
```bash
python db/init_db.py
```
Expected output:
```
  * categories      :   6 rows
  * menu_items      :  18 rows
  * customers       :  11 rows
  * employees       :   5 rows
  * orders          :  28 rows
  * order_items     :  57 rows
  * payments        :  28 rows
Database initialization completed successfully!
```

### Step 6: Launch the Web Application
Start the web application using either method:
- **Option A (One-Click Runner):**
  Double-click `run_project.bat` or `run_web.bat` in File Explorer.
- **Option B (Terminal):**
  ```bash
  python main.py
  ```
  *(or `python web/app.py`)*

Your browser will automatically open to:
```
http://127.0.0.1:5000
```

### Step 7: Run Automated Tests
Verify all business rules, database constraints, and web routes:
```bash
pytest tests/test_validators.py tests/test_web_app.py
```
Or run the full test suite when MySQL is active:
```bash
pytest
```

---

## 🗄️ Database Schema & Key Concepts

The system database consists of **7 normalized tables** in Third Normal Form (3NF):

1. **`categories`**: Menu categories (Beverages, South Indian, Snacks, Meals, etc.) with unique names.
2. **`menu_items`**: Catalog items with category FK, positive price constraint (`CHECK price > 0`), and availability toggle.
3. **`customers`**: Registered patrons with unique phone numbers (nullable order link for walk-ins).
4. **`employees`**: Cashiers and kitchen staff handling orders.
5. **`orders`**: Transaction headers tracking `customer_id`, `employee_id`, `order_status`, and `total_amount`.
6. **`order_items`**: Bridge table resolving Many-to-Many between Orders and Menu Items with `ON DELETE CASCADE`.
7. **`payments`**: Payment records with a strict `UNIQUE(order_id)` constraint enforcing exactly one payment per order.

### ⚖️ Revenue Accounting Rule (College Viva Concept)
> **"Revenue counts only Completed orders with Paid payments. Cancelled, unpaid, and refunded orders are excluded."**
- Each order is counted at most once (`COUNT(DISTINCT o.order_id)`).
- Line item amounts reconcile exactly with header totals.

---

## 📊 Modules & Web Views

| Module | Features |
| :--- | :--- |
| **📊 Dashboard** | Live KPI metric cards (Today's Sales, Orders Count, Active Items, Pending Orders), recent orders data table, and 7-day revenue bar chart powered by Chart.js. |
| **🏷️ Categories** | Add, edit, search, and delete categories with foreign key protection (cannot delete categories containing menu items). |
| **🍕 Menu Items** | Full item catalog with price validation, availability toggle, category assignment, and modal forms. |
| **👥 Customers** | Customer directory with 10-digit Indian phone number validation and live search. |
| **👨‍💼 Employees** | Staff directory with role management (Cashier / Kitchen Staff / Manager) and active status toggling. |
| **🛒 Orders (POS)** | Live Point of Sale grid with visual item cards, real-time cart, total price calculation, walk-in customer support, and order status lifecycle transition manager. |
| **💳 Payments** | Cashier reconciliation interface with unpaid order selector, automatic total population, duplicate payment guard, and searchable payment ledger. |
| **📈 Reports** | 4-tab interactive reporting center (Daily Sales, Popular Items, Order History, Date-wise Sales) with interactive Chart.js charts and PDF/CSV export support. |

---

## 🛠️ Troubleshooting & Common Errors

### 1. `Error 1045 (28000): Access denied for user 'root'@'localhost'`
- **Cause:** Incorrect database credentials in `.env`.
- **Solution:** In XAMPP, the default `root` user has **no password**. Open `.env` and set:
  ```env
  DB_USER=root
  DB_PASSWORD=
  ```

### 2. `Error 2003: Can't connect to MySQL server on 'localhost:3306'`
- **Cause:** MySQL is not running.
- **Solution:** Open the **XAMPP Control Panel** and click the **Start** button next to **MySQL**. The green indicator should show port **3306**.

### 3. `Address already in use: Port 5000`
- **Cause:** Another process or previous web server instance is running on port 5000.
- **Solution:** Stop the existing process using `Ctrl+C` in its terminal, or close the previous terminal window.
