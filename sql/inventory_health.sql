-- Inventory health: overstock, stockouts, and shelf-age distribution.

-- :name overstock
-- Heavy piles that have been sitting: 6+ on hand and 60+ days in stock
-- at the latest snapshot.
WITH latest AS (
    SELECT * FROM inventory
    WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
)
SELECT
    l.location,
    p.artist,
    p.title,
    p.genre,
    l.quantity_on_hand,
    l.days_in_stock
FROM latest l
JOIN products p USING (product_id)
WHERE l.quantity_on_hand >= 6
  AND l.days_in_stock >= 60
ORDER BY l.days_in_stock DESC;

-- :name stockouts
-- Zero on hand at the latest snapshot for products with recent demand
-- (sold in the last 60 days anywhere). These are lost-sale risks.
WITH latest AS (
    SELECT * FROM inventory
    WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
),
recent_demand AS (
    SELECT product_id, SUM(quantity) AS units_60d
    FROM sales
    WHERE sale_date >= date((SELECT MAX(sale_date) FROM sales), '-60 days')
    GROUP BY product_id
)
SELECT
    l.location,
    p.artist,
    p.title,
    p.genre,
    rd.units_60d AS sold_last_60d_all_stores
FROM latest l
JOIN products p USING (product_id)
JOIN recent_demand rd USING (product_id)
WHERE l.quantity_on_hand = 0
ORDER BY rd.units_60d DESC;

-- :name aging_buckets
-- How old is the stock on shelves right now? Share of on-hand units by age.
WITH latest AS (
    SELECT * FROM inventory
    WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
      AND quantity_on_hand > 0
)
SELECT
    CASE
        WHEN days_in_stock <= 30 THEN 'a. 0-30 days'
        WHEN days_in_stock <= 60 THEN 'b. 31-60 days'
        WHEN days_in_stock <= 90 THEN 'c. 61-90 days'
        ELSE 'd. 90+ days'
    END                                             AS age_bucket,
    SUM(quantity_on_hand)                           AS units,
    ROUND(100.0 * SUM(quantity_on_hand)
        / (SELECT SUM(quantity_on_hand) FROM latest), 1) AS pct_of_units
FROM latest
GROUP BY age_bucket
ORDER BY age_bucket;
