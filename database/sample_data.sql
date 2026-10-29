-- ==============================================================================
-- CANTEEN MANAGEMENT SYSTEM - COMPREHENSIVE SAMPLE DATA
-- ==============================================================================
-- Internally consistent data across all 7 tables for college viva demonstrations.
-- Mathematical Integrity Guaranteed:
-- 1. order.total_amount == SUM(order_items.subtotal) for each order.
-- 2. payment.amount == order.total_amount for each payment.
-- 3. Cancelled orders have Refunded payments (NOT Paid).
-- 4. Spans 12 distinct dates (2026-10-14 through 2026-10-25) across all 5 order statuses.
-- ==============================================================================

USE canteen_db;

-- ------------------------------------------------------------------------------
-- 1. Insert Categories (6 master categories)
-- ------------------------------------------------------------------------------
INSERT INTO categories (category_id, category_name, description) VALUES
(1, 'Beverages', 'Hot and cold teas, coffees, juices, and soft drinks'),
(2, 'South Indian', 'Traditional dosas, idlis, vadas, and morning tiffins'),
(3, 'Snacks & Quick Bites', 'Crispy samosas, puffs, sandwiches, and cutlets'),
(4, 'Main Course & Meals', 'Lunch thalis, fried rice, noodles, and combos'),
(5, 'Breads & Curries', 'Rotis, parathas, naans, and rich gravy curries'),
(6, 'Desserts & Sweets', 'Ice creams, gulab jamuns, pastries, and sweet treats');

-- ------------------------------------------------------------------------------
-- 2. Insert Menu Items (18 items, price > 0, DECIMAL(10,2))
-- ------------------------------------------------------------------------------
INSERT INTO menu_items (item_id, category_id, item_name, description, price, is_available) VALUES
(1, 1, 'Masala Chai', 'Fresh brewed spiced Indian milk tea', 15.00, 1),
(2, 1, 'Filter Coffee', 'South Indian decoction filter coffee', 20.00, 1),
(3, 1, 'Cold Coffee', 'Chilled blended creamy coffee', 45.00, 1),
(4, 1, 'Fresh Lime Soda', 'Refreshing sweet and salty soda', 30.00, 1),
(5, 2, 'Masala Dosa', 'Crispy dosa with spiced potato filling & chutney', 55.00, 1),
(6, 2, 'Idli Sambar (2 pcs)', 'Steamed rice cakes served with hot sambar', 35.00, 1),
(7, 2, 'Medu Vada (2 pcs)', 'Crispy savory lentil donuts served with sambar', 40.00, 1),
(8, 3, 'Veg Samosa (2 pcs)', 'Crispy pastry filled with potato & green peas', 25.00, 1),
(9, 3, 'Veg Grilled Sandwich', 'Toasted vegetable sandwich with cheese & mint chutney', 60.00, 1),
(10, 3, 'Paneer Puff', 'Flaky pastry stuffed with seasoned paneer', 30.00, 1),
(11, 4, 'Executive Veg Thali', 'Rice, 2 rotis, paneer sabzi, dal, curd & sweet', 120.00, 1),
(12, 4, 'Veg Fried Rice', 'Wok-tossed rice with fresh garden vegetables', 80.00, 1),
(13, 4, 'Hakka Noodles', 'Stir-fried noodles with crunchy cabbage & peppers', 85.00, 1),
(14, 5, 'Aloo Paratha with Curd', 'Whole wheat flatbread stuffed with spiced potato', 50.00, 1),
(15, 5, 'Paneer Butter Masala Combo', 'Rich cottage cheese curry with 2 butter naans', 110.00, 1),
(16, 5, 'Chole Bhature (2 pcs)', 'Spicy chickpea curry with fluffy fried bhature', 75.00, 1),
(17, 6, 'Gulab Jamun (2 pcs)', 'Warm milk dumplings soaked in rose sugar syrup', 35.00, 1),
(18, 6, 'Chocolate Brownie', 'Warm chocolate fudge brownie with chocolate sauce', 65.00, 1);

-- ------------------------------------------------------------------------------
-- 3. Insert Customers (11 customers with unique phone & optional email)
-- ------------------------------------------------------------------------------
INSERT INTO customers (customer_id, customer_name, phone, email) VALUES
(1, 'Aarav Patel', '9811122233', 'aarav.patel@college.edu'),
(2, 'Priya Sharma', '9822233344', 'priya.sharma@college.edu'),
(3, 'Rahul Verma', '9833344455', 'rahul.verma@college.edu'),
(4, 'Ananya Iyer', '9844455566', 'ananya.iyer@college.edu'),
(5, 'Dr. R. K. Gupta', '9855566677', 'rkgupta@college.edu'),
(6, 'Prof. Sunita Rao', '9866677788', 'sunita.rao@college.edu'),
(7, 'Vikram Malhotra', '9877788899', 'vikram.m@college.edu'),
(8, 'Neha Kulkarni', '9888899900', 'neha.k@college.edu'),
(9, 'Rohan Desai', '9899900011', 'rohan.desai@college.edu'),
(10, 'Tanvi Reddy', '9700011122', 'tanvi.reddy@college.edu'),
(11, 'Kunal Joshi', '9711122233', NULL);

-- ------------------------------------------------------------------------------
-- 4. Insert Employees (5 staff/cashiers/managers)
-- ------------------------------------------------------------------------------
INSERT INTO employees (employee_id, employee_name, role, phone, is_active) VALUES
(1, 'Suresh Chandra', 'Manager', '9876543210', 1),
(2, 'Ramesh Kumar', 'Cashier', '9876543211', 1),
(3, 'Deepak Singh', 'Cashier', '9876543212', 1),
(4, 'Kavita Devi', 'Kitchen Staff', '9876543213', 1),
(5, 'Manoj Yadav', 'Counter Staff', '9876543214', 1);

-- ------------------------------------------------------------------------------
-- 5. Insert Orders (28 orders across 12 distinct dates, covering all 5 statuses)
-- ------------------------------------------------------------------------------
INSERT INTO orders (order_id, customer_id, employee_id, order_datetime, order_status, total_amount) VALUES
(1, 1, 2, '2026-10-14 09:15:00', 'Completed', 75.00),
(2, 5, 2, '2026-10-14 13:30:00', 'Completed', 150.00),
(3, 2, 3, '2026-10-15 10:00:00', 'Completed', 85.00),
(4, NULL, 3, '2026-10-15 16:45:00', 'Completed', 80.00),
(5, 3, 2, '2026-10-16 11:20:00', 'Completed', 95.00),
(6, 6, 2, '2026-10-16 14:00:00', 'Completed', 145.00),
(7, 4, 3, '2026-10-17 09:30:00', 'Completed', 60.00),
(8, 7, 3, '2026-10-17 13:15:00', 'Completed', 110.00),
(9, 8, 2, '2026-10-18 10:15:00', 'Completed', 105.00),
(10, NULL, 2, '2026-10-18 17:00:00', 'Completed', 135.00),
(11, 9, 3, '2026-10-19 12:30:00', 'Completed', 105.00),
(12, 1, 3, '2026-10-19 14:10:00', 'Completed', 150.00),
(13, 10, 2, '2026-10-20 09:45:00', 'Completed', 70.00),
(14, 5, 2, '2026-10-20 13:40:00', 'Completed', 310.00),
(15, 11, 3, '2026-10-21 11:00:00', 'Completed', 70.00),
(16, NULL, 3, '2026-10-21 15:30:00', 'Completed', 210.00),
(17, 2, 2, '2026-10-22 10:00:00', 'Completed', 95.00),
(18, 3, 2, '2026-10-22 13:00:00', 'Completed', 140.00),
(19, 4, 3, '2026-10-23 12:15:00', 'Completed', 140.00),
(20, NULL, 3, '2026-10-23 16:00:00', 'Cancelled', 90.00),
(21, 6, 2, '2026-10-24 10:30:00', 'Completed', 75.00),
(22, 7, 2, '2026-10-24 13:45:00', 'Completed', 155.00),
(23, 8, 3, '2026-10-24 17:30:00', 'Cancelled', 110.00),
(24, 9, 2, '2026-10-25 09:00:00', 'Completed', 90.00),
(25, 10, 2, '2026-10-25 11:15:00', 'Ready', 90.00),
(26, 1, 3, '2026-10-25 12:00:00', 'Preparing', 110.00),
(27, 2, 3, '2026-10-25 12:10:00', 'Pending', 130.00),
(28, NULL, 2, '2026-10-25 12:20:00', 'Ready', 130.00);

-- ------------------------------------------------------------------------------
-- 6. Insert Order Items (Audit unit_price and computed subtotals)
-- ------------------------------------------------------------------------------
INSERT INTO order_items (order_item_id, order_id, item_id, quantity, unit_price, subtotal) VALUES
-- Order 1: 55 + 20 = 75
(1, 1, 5, 1, 55.00, 55.00),
(2, 1, 2, 1, 20.00, 20.00),
-- Order 2: 120 + 30 = 150
(3, 2, 11, 1, 120.00, 120.00),
(4, 2, 4, 1, 30.00, 30.00),
-- Order 3: 70 + 15 = 85
(5, 3, 6, 2, 35.00, 70.00),
(6, 3, 1, 1, 15.00, 15.00),
-- Order 4: 50 + 30 = 80
(7, 4, 8, 2, 25.00, 50.00),
(8, 4, 1, 2, 15.00, 30.00),
-- Order 5: 50 + 45 = 95
(9, 5, 14, 1, 50.00, 50.00),
(10, 5, 3, 1, 45.00, 45.00),
-- Order 6: 110 + 35 = 145
(11, 6, 15, 1, 110.00, 110.00),
(12, 6, 17, 1, 35.00, 35.00),
-- Order 7: 40 + 20 = 60
(13, 7, 7, 1, 40.00, 40.00),
(14, 7, 2, 1, 20.00, 20.00),
-- Order 8: 80 + 30 = 110
(15, 8, 12, 1, 80.00, 80.00),
(16, 8, 4, 1, 30.00, 30.00),
-- Order 9: 60 + 45 = 105
(17, 9, 9, 1, 60.00, 60.00),
(18, 9, 3, 1, 45.00, 45.00),
-- Order 10: 90 + 45 = 135
(19, 10, 10, 3, 30.00, 90.00),
(20, 10, 1, 3, 15.00, 45.00),
-- Order 11: 75 + 30 = 105
(21, 11, 16, 1, 75.00, 75.00),
(22, 11, 4, 1, 30.00, 30.00),
-- Order 12: 85 + 65 = 150
(23, 12, 13, 1, 85.00, 85.00),
(24, 12, 18, 1, 65.00, 65.00),
-- Order 13: 55 + 15 = 70
(25, 13, 5, 1, 55.00, 55.00),
(26, 13, 1, 1, 15.00, 15.00),
-- Order 14: 240 + 70 = 310
(27, 14, 11, 2, 120.00, 240.00),
(28, 14, 17, 2, 35.00, 70.00),
-- Order 15: 50 + 20 = 70
(29, 15, 14, 1, 50.00, 50.00),
(30, 15, 2, 1, 20.00, 20.00),
-- Order 16: 120 + 90 = 210
(31, 16, 9, 2, 60.00, 120.00),
(32, 16, 3, 2, 45.00, 90.00),
-- Order 17: 35 + 40 + 20 = 95
(33, 17, 6, 1, 35.00, 35.00),
(34, 17, 7, 1, 40.00, 40.00),
(35, 17, 2, 1, 20.00, 20.00),
-- Order 18: 75 + 65 = 140
(36, 18, 16, 1, 75.00, 75.00),
(37, 18, 18, 1, 65.00, 65.00),
-- Order 19: 110 + 30 = 140
(38, 19, 15, 1, 110.00, 110.00),
(39, 19, 4, 1, 30.00, 30.00),
-- Order 20: 50 + 40 = 90
(40, 20, 8, 2, 25.00, 50.00),
(41, 20, 2, 2, 20.00, 40.00),
-- Order 21: 55 + 20 = 75
(42, 21, 5, 1, 55.00, 55.00),
(43, 21, 2, 1, 20.00, 20.00),
-- Order 22: 120 + 35 = 155
(44, 22, 11, 1, 120.00, 120.00),
(45, 22, 17, 1, 35.00, 35.00),
-- Order 23: 65 + 45 = 110
(46, 23, 18, 1, 65.00, 65.00),
(47, 23, 3, 1, 45.00, 45.00),
-- Order 24: 70 + 20 = 90
(48, 24, 6, 2, 35.00, 70.00),
(49, 24, 2, 1, 20.00, 20.00),
-- Order 25: 60 + 30 = 90
(50, 25, 9, 1, 60.00, 60.00),
(51, 25, 4, 1, 30.00, 30.00),
-- Order 26: 80 + 30 = 110
(52, 26, 12, 1, 80.00, 80.00),
(53, 26, 10, 1, 30.00, 30.00),
-- Order 27: 85 + 45 = 130
(54, 27, 13, 1, 85.00, 85.00),
(55, 27, 3, 1, 45.00, 45.00),
-- Order 28: 100 + 30 = 130
(56, 28, 14, 2, 50.00, 100.00),
(57, 28, 1, 2, 15.00, 30.00);

-- ------------------------------------------------------------------------------
-- 7. Insert Payments (Exact 1:1 match with orders, Cancelled orders are Refunded)
-- ------------------------------------------------------------------------------
INSERT INTO payments (payment_id, order_id, payment_method, amount, payment_status, payment_datetime) VALUES
(1, 1, 'Cash', 75.00, 'Paid', '2026-10-14 09:16:00'),
(2, 2, 'UPI', 150.00, 'Paid', '2026-10-14 13:31:00'),
(3, 3, 'UPI', 85.00, 'Paid', '2026-10-15 10:01:00'),
(4, 4, 'Cash', 80.00, 'Paid', '2026-10-15 16:46:00'),
(5, 5, 'UPI', 95.00, 'Paid', '2026-10-16 11:21:00'),
(6, 6, 'UPI', 145.00, 'Paid', '2026-10-16 14:01:00'),
(7, 7, 'Cash', 60.00, 'Paid', '2026-10-17 09:31:00'),
(8, 8, 'UPI', 110.00, 'Paid', '2026-10-17 13:16:00'),
(9, 9, 'UPI', 105.00, 'Paid', '2026-10-18 10:16:00'),
(10, 10, 'Cash', 135.00, 'Paid', '2026-10-18 17:01:00'),
(11, 11, 'Cash', 105.00, 'Paid', '2026-10-19 12:31:00'),
(12, 12, 'UPI', 150.00, 'Paid', '2026-10-19 14:11:00'),
(13, 13, 'UPI', 70.00, 'Paid', '2026-10-20 09:46:00'),
(14, 14, 'UPI', 310.00, 'Paid', '2026-10-20 13:41:00'),
(15, 15, 'Cash', 70.00, 'Paid', '2026-10-21 11:01:00'),
(16, 16, 'UPI', 210.00, 'Paid', '2026-10-21 15:31:00'),
(17, 17, 'UPI', 95.00, 'Paid', '2026-10-22 10:01:00'),
(18, 18, 'Cash', 140.00, 'Paid', '2026-10-22 13:01:00'),
(19, 19, 'UPI', 140.00, 'Paid', '2026-10-23 12:16:00'),
(20, 20, 'Cash', 90.00, 'Refunded', '2026-10-23 16:05:00'),
(21, 21, 'UPI', 75.00, 'Paid', '2026-10-24 10:31:00'),
(22, 22, 'Cash', 155.00, 'Paid', '2026-10-24 13:46:00'),
(23, 23, 'UPI', 110.00, 'Refunded', '2026-10-24 17:35:00'),
(24, 24, 'UPI', 90.00, 'Paid', '2026-10-25 09:01:00'),
(25, 25, 'UPI', 90.00, 'Paid', '2026-10-25 11:16:00'),
(26, 26, 'Cash', 110.00, 'Paid', '2026-10-25 12:01:00'),
(27, 27, 'UPI', 130.00, 'Pending', '2026-10-25 12:10:00'),
(28, 28, 'Cash', 130.00, 'Paid', '2026-10-25 12:21:00');
