-- RevoShop API - Sample Queries
-- Checkpoint 1

-- 1. A query combining WHERE, ORDER BY, and LIMIT.
-- This query retrieves the top 3 most expensive products that are currently in stock (stock > 0),
-- ordered by price descending.
SELECT 
    p.name AS product_name, 
    c.name AS category_name, 
    p.price, 
    p.stock
FROM 
    products p
JOIN 
    categories c ON p.category_id = c.id
WHERE 
    p.stock > 0
ORDER BY 
    p.price DESC
LIMIT 3;

-- 2. (Optional) A query to see all orders with their total items and amount for a specific user
SELECT 
    o.id AS order_id,
    u.username,
    o.total_amount,
    o.status,
    o.created_at,
    SUM(oi.quantity) as total_items
FROM 
    orders o
JOIN 
    users u ON o.user_id = u.id
JOIN 
    order_items oi ON o.id = oi.order_id
WHERE 
    u.username = 'john_doe'
GROUP BY 
    o.id, u.username, o.total_amount, o.status, o.created_at
ORDER BY 
    o.created_at DESC;
