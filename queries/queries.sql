-- 1. A query combining WHERE, ORDER BY, and LIMIT.
-- Retrieves top 3 most expensive in-stock clothing items for Women, with category info, by price descending.
SELECT 
    p.name AS product_name, 
    COALESCE(c.name, 'Uncategorized') AS category_name, 
    p.price, 
    p.size,
    p.color,
    p.material,
    p.stock
FROM 
    products p
LEFT JOIN 
    categories c ON p.category_id = c.id
WHERE 
    p.stock > 0
    AND p.gender = 'Women'
    AND p.is_active = TRUE
ORDER BY 
    p.price DESC
LIMIT 3;

-- 2. A query to see all orders with their total items, amount, and purchased size/color for a specific user
SELECT 
    o.id AS order_id,
    u.username,
    o.total_amount,
    o.status,
    o.created_at,
    COALESCE(SUM(oi.quantity), 0) AS total_items,
    STRING_AGG(p.name || ' (' || oi.size || '/' || oi.color || ')', ', ') AS items_summary
FROM 
    orders o
JOIN 
    users u ON o.user_id = u.id
LEFT JOIN 
    order_items oi ON o.id = oi.order_id
LEFT JOIN
    products p ON oi.product_id = p.id
WHERE 
    u.username = 'alice_smith'
GROUP BY 
    o.id, u.username, o.total_amount, o.status, o.created_at
ORDER BY 
    o.created_at DESC;
