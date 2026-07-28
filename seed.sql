-- RevoShop API - Sample Data
-- Checkpoint 1

-- 0. Reset Tables (Idempotent execution)
TRUNCATE TABLE order_items, orders, products, categories, users RESTART IDENTITY CASCADE;

-- 1. Insert Categories
INSERT INTO categories (name, description) VALUES
('Electronics', 'Gadgets, devices, and accessories'),
('Clothing', 'Apparel for men and women'),
('Home & Garden', 'Furniture, decor, and gardening tools');

-- 2. Insert Users
-- Note: Passwords are raw strings here for simplicity in DB testing, 
-- but in the actual application, they will be hashed (e.g., pbkdf2:sha256).
INSERT INTO users (username, email, password_hash) VALUES
('john_doe', 'john@example.com', 'hashed_password_1'),
('jane_smith', 'jane@example.com', 'hashed_password_2'),
('bob_builder', 'bob@example.com', 'hashed_password_3');

-- 3. Insert Products
INSERT INTO products (category_id, name, description, price, stock) VALUES
(1, 'Smartphone X', 'Latest smartphone with high-end camera', 999.99, 50),
(1, 'Wireless Earbuds', 'Noise-canceling true wireless earbuds', 149.50, 200),
(1, 'Gaming Laptop', 'Powerful laptop for gaming and rendering', 1599.00, 15),
(2, 'Classic T-Shirt', '100% cotton everyday t-shirt', 19.99, 500),
(2, 'Denim Jacket', 'Vintage style blue denim jacket', 59.90, 80),
(3, 'Desk Lamp', 'LED desk lamp with adjustable brightness', 25.00, 120),
(3, 'Ergonomic Chair', 'Comfortable chair for long working hours', 199.99, 30);

-- 4. Insert Orders
-- Assuming john_doe (id 1) and jane_smith (id 2) make orders
-- Note: status 'completed' diganti menjadi 'delivered' agar sesuai dengan CHECK constraint
INSERT INTO orders (user_id, total_amount, status) VALUES
(1, 1149.49, 'delivered'),
(2, 59.90, 'pending'),
(1, 44.99, 'processing');

-- 5. Insert Order Items
-- Order 1: Smartphone X (1 x 999.99) + Wireless Earbuds (1 x 149.50) = 1149.49
INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES
(1, 1, 1, 999.99),
(1, 2, 1, 149.50);

-- Order 2: Denim Jacket (1 x 59.90) = 59.90
INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES
(2, 5, 1, 59.90);

-- Order 3: Classic T-Shirt (1 x 19.99) + Desk Lamp (1 x 25.00) = 44.99
INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES
(3, 4, 1, 19.99),
(3, 6, 1, 25.00);
