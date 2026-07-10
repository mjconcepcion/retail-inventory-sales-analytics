-- Sales performance: where the revenue comes from.

-- :name monthly_revenue
-- Revenue and units by month across all locations. Shows seasonality
-- (December gift rush, April Record Store Day).
SELECT
    strftime('%Y-%m', sale_date)  AS month,
    ROUND(SUM(net_amount), 2)     AS revenue,
    SUM(quantity)                 AS units
FROM sales
GROUP BY month
ORDER BY month;

-- :name revenue_by_location
SELECT
    location,
    ROUND(SUM(net_amount), 2)                    AS revenue,
    SUM(quantity)                                AS units,
    ROUND(SUM(net_amount) / SUM(quantity), 2)    AS avg_net_per_unit
FROM sales
GROUP BY location
ORDER BY revenue DESC;

-- :name revenue_by_genre
SELECT
    p.genre,
    ROUND(SUM(s.net_amount), 2)  AS revenue,
    SUM(s.quantity)              AS units
FROM sales s
JOIN products p USING (product_id)
GROUP BY p.genre
ORDER BY revenue DESC;

-- :name genre_by_location
-- Genre mix per store — surfaces local taste (e.g., jazz/latin at Dania).
SELECT
    s.location,
    p.genre,
    ROUND(SUM(s.net_amount), 2)  AS revenue,
    SUM(s.quantity)              AS units
FROM sales s
JOIN products p USING (product_id)
GROUP BY s.location, p.genre
ORDER BY s.location, revenue DESC;
