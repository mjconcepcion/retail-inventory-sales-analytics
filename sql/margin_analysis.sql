-- Gross margin: which parts of the catalog actually make money.

-- :name margin_by_condition
-- The used-vs-new story. Used stock is bought cheap; margin % tells the tale.
SELECT
    p.condition,
    ROUND(SUM(s.net_amount), 2)                          AS revenue,
    ROUND(SUM(s.quantity * (s.unit_price - s.discount - p.cost)), 2) AS gross_profit,
    ROUND(100.0 * SUM(s.quantity * (s.unit_price - s.discount - p.cost))
        / SUM(s.net_amount), 1)                          AS margin_pct
FROM sales s
JOIN products p USING (product_id)
GROUP BY p.condition
ORDER BY margin_pct DESC;

-- :name margin_by_format_condition
SELECT
    p.format,
    p.condition,
    SUM(s.quantity)                                      AS units,
    ROUND(SUM(s.net_amount), 2)                          AS revenue,
    ROUND(SUM(s.quantity * (s.unit_price - s.discount - p.cost)), 2) AS gross_profit,
    ROUND(100.0 * SUM(s.quantity * (s.unit_price - s.discount - p.cost))
        / SUM(s.net_amount), 1)                          AS margin_pct
FROM sales s
JOIN products p USING (product_id)
GROUP BY p.format, p.condition
ORDER BY gross_profit DESC;

-- :name margin_by_genre
SELECT
    p.genre,
    ROUND(SUM(s.net_amount), 2)                          AS revenue,
    ROUND(SUM(s.quantity * (s.unit_price - s.discount - p.cost)), 2) AS gross_profit,
    ROUND(100.0 * SUM(s.quantity * (s.unit_price - s.discount - p.cost))
        / SUM(s.net_amount), 1)                          AS margin_pct
FROM sales s
JOIN products p USING (product_id)
GROUP BY p.genre
ORDER BY gross_profit DESC;
