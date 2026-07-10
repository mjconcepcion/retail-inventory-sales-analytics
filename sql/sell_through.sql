-- Sell-through: how fast stock converts to sales.
-- sell_through = units sold / (units sold + units still on hand).
-- High = stock moves; low = shelf furniture.

-- :name sell_through_by_genre
WITH latest AS (
    SELECT product_id, SUM(quantity_on_hand) AS on_hand
    FROM inventory
    WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
    GROUP BY product_id
),
sold AS (
    SELECT product_id, SUM(quantity) AS units_sold
    FROM sales
    GROUP BY product_id
)
SELECT
    p.genre,
    SUM(COALESCE(s.units_sold, 0))                     AS units_sold,
    SUM(COALESCE(l.on_hand, 0))                        AS units_on_hand,
    ROUND(100.0 * SUM(COALESCE(s.units_sold, 0))
        / NULLIF(SUM(COALESCE(s.units_sold, 0)) + SUM(COALESCE(l.on_hand, 0)), 0), 1)
                                                       AS sell_through_pct
FROM products p
LEFT JOIN sold s USING (product_id)
LEFT JOIN latest l USING (product_id)
GROUP BY p.genre
ORDER BY sell_through_pct DESC;

-- :name sell_through_by_location
WITH latest AS (
    SELECT location, product_id, quantity_on_hand
    FROM inventory
    WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
),
sold AS (
    SELECT location, product_id, SUM(quantity) AS units_sold
    FROM sales
    GROUP BY location, product_id
)
SELECT
    COALESCE(l.location, s.location)                   AS location,
    SUM(COALESCE(s.units_sold, 0))                     AS units_sold,
    SUM(COALESCE(l.quantity_on_hand, 0))               AS units_on_hand,
    ROUND(100.0 * SUM(COALESCE(s.units_sold, 0))
        / NULLIF(SUM(COALESCE(s.units_sold, 0)) + SUM(COALESCE(l.quantity_on_hand, 0)), 0), 1)
                                                       AS sell_through_pct
FROM latest l
FULL OUTER JOIN sold s
     ON l.location = s.location AND l.product_id = s.product_id
GROUP BY COALESCE(l.location, s.location)
ORDER BY sell_through_pct DESC;
