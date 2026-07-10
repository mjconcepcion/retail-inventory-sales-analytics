-- Schema for the retail analytics database (SQLite).
-- Loaded by src/load_db.py from the cleaned CSVs in data/processed/.

DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    product_id    TEXT PRIMARY KEY,
    sku           TEXT,
    artist        TEXT NOT NULL,
    title         TEXT NOT NULL,
    format        TEXT NOT NULL,          -- LP / CD / 7" / Cassette
    genre         TEXT NOT NULL,
    condition     TEXT NOT NULL,          -- New / Used
    cost          REAL NOT NULL,          -- what the store paid
    price         REAL NOT NULL,          -- sticker price
    release_year  INTEGER
);

CREATE TABLE sales (
    sale_id     TEXT PRIMARY KEY,
    sale_date   TEXT NOT NULL,            -- ISO date
    location    TEXT NOT NULL,
    product_id  TEXT NOT NULL REFERENCES products(product_id),
    quantity    INTEGER NOT NULL,
    unit_price  REAL NOT NULL,
    discount    REAL NOT NULL DEFAULT 0,
    net_amount  REAL NOT NULL             -- quantity * (unit_price - discount)
);

CREATE TABLE inventory (
    snapshot_date     TEXT NOT NULL,      -- ISO date, monthly snapshots
    location          TEXT NOT NULL,
    product_id        TEXT NOT NULL REFERENCES products(product_id),
    quantity_on_hand  INTEGER NOT NULL,
    days_in_stock     INTEGER NOT NULL,
    reorder_level     INTEGER NOT NULL,
    PRIMARY KEY (snapshot_date, location, product_id)
);

CREATE INDEX idx_sales_product   ON sales(product_id);
CREATE INDEX idx_sales_date      ON sales(sale_date);
CREATE INDEX idx_sales_location  ON sales(location);
CREATE INDEX idx_inventory_product ON inventory(product_id);
