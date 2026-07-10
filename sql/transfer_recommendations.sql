-- Transfer recommendations: the money query.
-- Inventory sitting at one store while another store is out of stock and
-- has demonstrated demand. Moving it costs a car trip, not a purchase order.

-- :name transfer_recommendations
WITH latest AS (
    SELECT * FROM inventory
    WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
),
demand_at_location AS (
    -- 90-day unit demand per product per location: prioritizes transfers
    -- toward stores that actually sell the title.
    SELECT
        location,
        product_id,
        SUM(quantity) AS units_90d
    FROM sales
    WHERE sale_date >= date((SELECT MAX(sale_date) FROM sales), '-90 days')
    GROUP BY location, product_id
)
SELECT
    overstock.location                    AS from_location,
    understock.location                   AS to_location,
    p.artist,
    p.title,
    p.format,
    p.genre,
    overstock.quantity_on_hand            AS from_qty,
    overstock.days_in_stock               AS from_days_sitting,
    COALESCE(d.units_90d, 0)              AS to_location_demand_90d,
    -- Move half the pile, keep at least the reorder level behind
    MIN(overstock.quantity_on_hand - overstock.reorder_level,
        (overstock.quantity_on_hand + 1) / 2)  AS suggested_transfer_qty,
    ROUND(COALESCE(d.units_90d, 0) * p.price, 2) AS est_90d_revenue_at_dest
FROM latest overstock
JOIN latest understock
     ON  overstock.product_id = understock.product_id
     AND overstock.location <> understock.location
JOIN products p ON p.product_id = overstock.product_id
LEFT JOIN demand_at_location d
     ON  d.location = understock.location
     AND d.product_id = understock.product_id
WHERE overstock.quantity_on_hand >= 5
  AND understock.quantity_on_hand = 0
ORDER BY est_90d_revenue_at_dest DESC, from_days_sitting DESC;
