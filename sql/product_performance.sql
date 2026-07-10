-- Product performance: heroes and dead weight.

-- :name top_products
-- Top 15 titles by revenue over the full period.
SELECT
    p.artist,
    p.title,
    p.format,
    p.genre,
    p.condition,
    SUM(s.quantity)             AS units,
    ROUND(SUM(s.net_amount), 2) AS revenue
FROM sales s
JOIN products p USING (product_id)
GROUP BY p.product_id
ORDER BY revenue DESC
LIMIT 15;

-- :name dead_stock
-- Titles sitting on shelves (latest snapshot) with zero sales in the last
-- 90 days of the sales window. Candidates for markdown or promo bins.
WITH latest AS (
    SELECT * FROM inventory
    WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
),
recent_sales AS (
    SELECT DISTINCT product_id
    FROM sales
    WHERE sale_date >= date((SELECT MAX(sale_date) FROM sales), '-90 days')
)
SELECT
    l.location,
    p.artist,
    p.title,
    p.genre,
    p.condition,
    l.quantity_on_hand,
    l.days_in_stock,
    ROUND(l.quantity_on_hand * p.cost, 2) AS cost_tied_up
FROM latest l
JOIN products p USING (product_id)
WHERE l.quantity_on_hand > 0
  AND l.product_id NOT IN (SELECT product_id FROM recent_sales)
ORDER BY cost_tied_up DESC
LIMIT 25;
