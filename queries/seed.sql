-- RevoFashion API - Seed Data
-- Fashion/Clothing Online Store (Uniqlo-inspired)

-- 0. Reset Tables (Idempotent execution)
TRUNCATE TABLE order_items, orders, product_images, products, categories, users RESTART IDENTITY CASCADE;

-- 1. Insert Categories
INSERT INTO categories (name, description, is_active) VALUES
('T-Shirts', 'Casual and everyday t-shirts, crew necks, and graphic tees', TRUE),
('Shirts & Blouses', 'Formal and casual shirts, oxford shirts, and blouses', TRUE),
('Pants & Jeans', 'Bottoms including denim, chinos, and ankle pants', TRUE),
('Outerwear', 'Jackets, coats, down jackets, and hoodies', TRUE),
('Dresses & Skirts', 'Dresses, skirts, and jumpsuits for women', TRUE),
('Activewear', 'Sportswear, dry-EX, and athleisure clothing', TRUE),
('Innerwear & Loungewear', 'Underwear, socks, heattech, and home wear', TRUE),
('Discontinued Collection', 'Past season items no longer sold', FALSE);

-- 2. Insert Users
INSERT INTO users (username, email, password_hash, role, is_active) VALUES
('superadmin_user', 'superadmin@revofashion.com', 'hashed_password_sa', 'superadmin', TRUE),
('admin_user', 'admin@revofashion.com', 'hashed_password_admin', 'admin', TRUE),
('alice_smith', 'alice@example.com', 'hashed_password_alice', 'customer', TRUE),
('deactivated_user', 'deactivated@example.com', 'hashed_password_deactivated', 'customer', FALSE);

-- 3. Insert Products (Fashion items, Uniqlo-inspired)
INSERT INTO products (category_id, name, description, price, stock, size, color, material, gender, sku, is_active) VALUES
-- T-Shirts
(1, 'AIRism Cotton Crew Neck T-Shirt', 'Smooth AIRism cotton blend with quick-dry and anti-odor technology.', 14.90, 200, 'M', 'White', '58% Cotton, 38% Polyester, 4% Spandex', 'Men', 'RF-TS-001', TRUE),
(1, 'Supima Cotton Crew Neck T-Shirt', 'Premium Supima cotton with a luxuriously soft feel.', 19.90, 150, 'L', 'Navy', '100% Supima Cotton', 'Men', 'RF-TS-002', TRUE),
(1, 'Oversized Cropped T-Shirt', 'Relaxed oversized fit with a slightly cropped length.', 19.90, 120, 'S', 'Black', '100% Cotton', 'Women', 'RF-TS-003', TRUE),
-- Shirts & Blouses
(2, 'Oxford Slim-Fit Long Sleeve Shirt', 'Classic button-down oxford shirt with a modern slim fit.', 29.90, 80, 'M', 'Light Blue', '100% Cotton', 'Men', 'RF-SH-001', TRUE),
(2, 'Rayon Long Sleeve Blouse', 'Elegant drape with a smooth rayon finish.', 29.90, 90, 'M', 'Off White', '100% Rayon', 'Women', 'RF-SH-002', TRUE),
-- Pants & Jeans
(3, 'EZY Ankle Pants', 'Incredibly comfortable ankle-length pants with elastic waist.', 39.90, 100, 'L', 'Dark Gray', '68% Polyester, 28% Rayon, 4% Spandex', 'Men', 'RF-PT-001', TRUE),
(3, 'Ultra Stretch High-Rise Jeans', 'High-rise skinny jeans with ultra stretch denim.', 49.90, 70, 'S', 'Blue', '86% Cotton, 12% Polyester, 2% Spandex', 'Women', 'RF-PT-002', TRUE),
-- Outerwear
(4, 'Ultra Light Down Jacket', 'Incredibly lightweight and warm premium down jacket.', 79.90, 50, 'M', 'Olive', '100% Nylon (Shell), 90% Down 10% Feather (Fill)', 'Unisex', 'RF-OW-001', TRUE),
(4, 'Pocketable UV Protection Parka', 'Lightweight parka with UPF 50+ sun protection.', 49.90, 60, 'M', 'Beige', '100% Polyester', 'Women', 'RF-OW-002', TRUE),
(4, 'Dry Stretch Full-Zip Hoodie', 'Quick-drying hoodie with 4-way stretch fabric.', 39.90, 85, 'L', 'Black', '88% Polyester, 12% Spandex', 'Men', 'RF-OW-003', TRUE),
-- Dresses & Skirts
(5, 'Mercerized Cotton A-Line Dress', 'Elegant A-line dress with a subtle sheen.', 39.90, 40, 'M', 'Dark Green', '100% Cotton', 'Women', 'RF-DR-001', TRUE),
-- Activewear
(6, 'DRY-EX Crew Neck T-Shirt', 'Ultra-fast drying performance tee with mesh ventilation.', 19.90, 180, 'M', 'Red', '100% Polyester', 'Unisex', 'RF-AW-001', TRUE),
(6, 'Ultra Stretch Active Jogger Pants', 'Flexible jogger pants with 4-way stretch.', 39.90, 75, 'M', 'Navy', '85% Nylon, 15% Spandex', 'Men', 'RF-AW-002', TRUE),
-- Innerwear & Loungewear
(7, 'HEATTECH Crew Neck Long Sleeve T-Shirt', 'Bio-warming technology that converts body moisture into heat.', 14.90, 300, 'M', 'Black', '43% Polyester, 35% Acrylic, 15% Rayon, 7% Spandex', 'Unisex', 'RF-IW-001', TRUE),
(7, 'AIRism Cotton Ribbed Tank Top', 'Comfortable ribbed tank top with AIRism technology.', 12.90, 160, 'S', 'White', '62% Cotton, 33% Polyester, 5% Spandex', 'Women', 'RF-IW-002', TRUE),
-- Discontinued
(8, 'Vintage Flannel Shirt (Discontinued)', 'Past season flannel shirt — no longer in production.', 34.90, 3, 'L', 'Red Plaid', '100% Cotton Flannel', 'Men', 'RF-DC-001', FALSE);

-- 4. Insert Orders
-- Order 1: alice_smith buys AIRism T-Shirt (M/White) + EZY Ankle Pants (L/Dark Gray) = 14.90 + 39.90 = 54.80
INSERT INTO orders (user_id, total_amount, status) VALUES
(3, 54.80, 'pending');

-- 5. Insert Order Items (with size/color at purchase)
INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase, size, color) VALUES
(1, 1, 1, 14.90, 'M', 'White'),
(1, 6, 1, 39.90, 'L', 'Dark Gray');
