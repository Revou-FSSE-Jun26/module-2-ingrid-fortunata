-- 1. A query combining WHERE, ORDER BY, and LIMIT.
-- Retrieves top 3 most expensive in-stock products with optional category check (LEFT JOIN) by price decending.
SELECT 
    p.name AS product_name, 
    COALESCE(c.name, 'Uncategorized') AS category_name, 
    p.price, 
    p.stock
FROM 
    products p
LEFT JOIN 
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
    COALESCE(SUM(oi.quantity), 0) AS total_items
FROM 
    orders o
JOIN 
    users u ON o.user_id = u.id
LEFT JOIN 
    order_items oi ON o.id = oi.order_id
WHERE 
    u.username = 'sarah_mill'
GROUP BY 
    o.id, u.username, o.total_amount, o.status, o.created_at
ORDER BY 
    o.created_at DESC;
