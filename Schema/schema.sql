 
-- MenuIQ database schema (Phase 1, Step 2)
-- Run this once to create your tables:  psql -d menuiq -f schema.sql

-- Drop in reverse dependency order so re-running is safe.
DROP TABLE IF EXISTS order_lines;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS menu_items;

-- One row per menu item. `margin` is computed by the database itself, so it can
-- never drift out of sync with price and cost.
CREATE TABLE menu_items (
    item_id    INTEGER PRIMARY KEY,
    name       TEXT          NOT NULL,
    price      NUMERIC(6,2)  NOT NULL,
    food_cost  NUMERIC(6,2)  NOT NULL,
    category   TEXT          NOT NULL,
    margin     NUMERIC(6,2)  GENERATED ALWAYS AS (price - food_cost) STORED
);

-- The "header" of each receipt: one row per order, holding the timestamp.
CREATE TABLE orders (
    order_id    INTEGER   PRIMARY KEY,
    ordered_at  TIMESTAMP NOT NULL
);

-- The "detail" of each receipt: one row per item on an order.
-- unit_price is the price PAID at the time of sale (kept separately from the
-- menu's current price, because menu prices change over time).
CREATE TABLE order_lines (
    line_id     SERIAL        PRIMARY KEY,
    order_id    INTEGER       NOT NULL REFERENCES orders(order_id),
    item_id     INTEGER       NOT NULL REFERENCES menu_items(item_id),
    unit_price  NUMERIC(6,2)  NOT NULL
);

-- Indexes for the two access patterns your analytics will hammer:
CREATE INDEX idx_order_lines_order ON order_lines(order_id);  -- grouping into baskets
CREATE INDEX idx_order_lines_item  ON order_lines(item_id);   -- per-item aggregation
CREATE INDEX idx_orders_time       ON orders(ordered_at);     -- time-of-day analysis
