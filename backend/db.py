"""Database connection and data loading for MenuIQ analytics."""

from __future__ import annotations

import os
from typing import Tuple

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()


def get_engine() -> Engine:
    """Create a SQLAlchemy engine from DATABASE_URL in the environment."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Add it to your .env file.")
    return create_engine(database_url)


def load_transaction_data(
    engine: Engine | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load menu_items, orders, and order_lines from PostgreSQL into DataFrames.

    Returns:
        items_df: menu item catalog with generated margin column.
        orders_df: one row per order with ordered_at timestamp.
        lines_df: one row per sold item (order line).
    """
    engine = engine or get_engine()

    items_df = pd.read_sql("SELECT * FROM menu_items ORDER BY item_id", engine)
    orders_df = pd.read_sql("SELECT * FROM orders ORDER BY order_id", engine)
    lines_df = pd.read_sql("SELECT * FROM order_lines ORDER BY line_id", engine)

    for col in ("price", "food_cost", "margin", "unit_price"):
        if col in items_df.columns or col in lines_df.columns:
            target = items_df if col in items_df.columns else lines_df
            target[col] = pd.to_numeric(target[col], errors="coerce")

    return items_df, orders_df, lines_df
