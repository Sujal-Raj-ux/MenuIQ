"""
MenuIQ - load CSV data into PostgreSQL (Phase 1, Step 2)

Prerequisites:
  1. Postgres is running and a database named 'menuiq' exists.
  2. You ran schema.sql to create the tables.
  3. pip install psycopg2-binary

Run:  python load_data.py
(Set DATABASE_URL if your connection details differ from the default below.)
"""

import csv
import os

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os

load_dotenv()  # Loads variables from .env

database_url = os.getenv("DATABASE_URL")
# Edit this, or export DATABASE_URL, to match your machine.
DSN = os.environ.get("DATABASE_URL", database_url)
HERE = os.path.dirname(os.path.abspath(__file__))

def load():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()

    # --- 1. menu_items: straight copy from menu_items.csv
    with open(os.path.join(HERE, "menu_items.csv")) as f:
        items = [
            (int(r["item_id"]), r["name"], r["price"], r["food_cost"], r["category"])
            for r in csv.DictReader(f)
        ]
    execute_values(
        cur,
        "INSERT INTO menu_items (item_id, name, price, food_cost, category) VALUES %s",
        items,
    )

    # --- 2. orders + 3. order_lines, both derived from order_lines.csv
    # The receipts file repeats the timestamp on every line; we collapse it to
    # one row per order for the `orders` table.
    orders = {}
    lines = []
    with open(os.path.join(HERE, "order_lines.csv")) as f:
        for r in csv.DictReader(f):
            oid = int(r["order_id"])
            orders[oid] = r["ordered_at"]
            lines.append((oid, int(r["item_id"]), r["price"]))

    execute_values(
        cur,
        "INSERT INTO orders (order_id, ordered_at) VALUES %s",
        list(orders.items()),
    )
    execute_values(
        cur,
        "INSERT INTO order_lines (order_id, item_id, unit_price) VALUES %s",
        lines,
    )

    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {len(items)} menu items, {len(orders)} orders, {len(lines)} order lines.")


if __name__ == "__main__":
    load()