"""Parse and normalize uploaded transaction files into canonical DataFrames.

The analytics layer (Phase 2) expects two frames:
  - items_df: one row per menu item with item_id, name, price, food_cost,
    category, margin.
  - lines_df: one row per sold unit with order_id, item_id, unit_price.

A user upload won't match that shape exactly, so this module maps flexible
column names, validates the data, and builds those frames deterministically.
No metrics are invented here — margin requires a real cost (or margin) column.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

import pandas as pd

MAX_INPUT_ROWS = 200_000
MAX_EXPANDED_UNITS = 500_000

# Map of canonical column -> accepted source header synonyms (normalized).
_COLUMN_SYNONYMS: dict[str, tuple[str, ...]] = {
    "order_id": (
        "order_id", "order", "order_no", "order_number", "transaction_id",
        "transaction", "receipt_id", "receipt", "ticket_id", "ticket",
        "bill_id", "bill", "invoice_id", "invoice", "check_id", "check",
    ),
    "item_name": (
        "item_name", "item", "name", "product", "product_name", "menu_item",
        "description", "item_description", "dish",
    ),
    "price": (
        "price", "unit_price", "sale_price", "selling_price", "amount",
        "line_price", "item_price",
    ),
    "food_cost": (
        "food_cost", "cost", "unit_cost", "item_cost", "cogs", "cost_price",
    ),
    "margin": ("margin", "contribution_margin", "profit"),
    "category": ("category", "type", "group", "menu_category", "section"),
    "quantity": ("quantity", "qty", "count", "units", "amount_sold"),
}


class IngestError(ValueError):
    """Raised when an uploaded file cannot be parsed into valid analytics data."""


@dataclass
class IngestResult:
    items_df: pd.DataFrame
    lines_df: pd.DataFrame
    orders: int
    line_items: int
    distinct_items: int
    warnings: list[str] = field(default_factory=list)


def _normalize_header(name: str) -> str:
    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("__", "_")
    )


def _read_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    name = (filename or "").lower()
    try:
        if name.endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(file_bytes))
        return pd.read_csv(io.BytesIO(file_bytes))
    except Exception as exc:  # noqa: BLE001 - surface a clean message to the API
        raise IngestError(f"Could not read file '{filename}': {exc}") from exc


def _resolve_columns(df: pd.DataFrame) -> dict[str, str]:
    """Map normalized source headers to canonical column names."""
    normalized = {_normalize_header(c): c for c in df.columns}
    resolved: dict[str, str] = {}
    for canonical, synonyms in _COLUMN_SYNONYMS.items():
        for syn in synonyms:
            if syn in normalized:
                resolved[canonical] = normalized[syn]
                break
    return resolved


def parse_transactions(
    file_bytes: bytes,
    filename: str,
    cost_pct: float | None = None,
) -> IngestResult:
    """
    Parse an uploaded CSV/Excel of transactions into items_df and lines_df.

    Required columns (flexible names): order id, item name, price.
    Profitability requires one of: a food cost column, a margin column, or a
    caller-supplied cost_pct (an assumed food-cost percentage of price, 0-100).
    Optional: category, quantity.
    """
    df = _read_file(file_bytes, filename)
    if df.empty:
        raise IngestError("The uploaded file has no rows.")
    if len(df) > MAX_INPUT_ROWS:
        raise IngestError(
            f"File has {len(df):,} rows; the limit is {MAX_INPUT_ROWS:,}."
        )

    cols = _resolve_columns(df)
    warnings: list[str] = []

    if cost_pct is not None and not (0 <= cost_pct < 100):
        raise IngestError("Assumed food-cost percentage must be between 0 and 100.")

    missing = [c for c in ("order_id", "item_name", "price") if c not in cols]
    if missing:
        raise IngestError(
            "Missing required column(s): "
            + ", ".join(missing)
            + ". Expected an order id, item name, and price."
        )
    if "food_cost" not in cols and "margin" not in cols and cost_pct is None:
        raise IngestError(
            "Provide a 'food_cost' column (or a 'margin' column) so profitability "
            "can be computed — or set an assumed food-cost percentage on upload. "
            "Metrics are never estimated by the AI."
        )

    work = pd.DataFrame()
    work["order_id"] = df[cols["order_id"]].astype(str).str.strip()
    work["item_name"] = df[cols["item_name"]].astype(str).str.strip()
    work["price"] = pd.to_numeric(df[cols["price"]], errors="coerce")

    if "food_cost" in cols:
        work["food_cost"] = pd.to_numeric(df[cols["food_cost"]], errors="coerce")
    if "margin" in cols:
        work["margin_in"] = pd.to_numeric(df[cols["margin"]], errors="coerce")
    work["category"] = (
        df[cols["category"]].astype(str).str.strip()
        if "category" in cols
        else "uncategorized"
    )
    if "quantity" in cols:
        work["quantity"] = (
            pd.to_numeric(df[cols["quantity"]], errors="coerce").fillna(1).clip(lower=0)
        )
    else:
        work["quantity"] = 1

    before = len(work)
    work = work[(work["item_name"] != "") & (work["order_id"] != "")]
    work = work.dropna(subset=["price"])
    dropped = before - len(work)
    if dropped:
        warnings.append(f"Skipped {dropped} row(s) missing item, order id, or price.")
    if work.empty:
        raise IngestError("No valid rows remained after cleaning the file.")

    # Quantity drives units sold; expand to one row per unit so the analytics
    # layer's row counts equal units sold. Fractional/zero quantities round.
    work["quantity"] = work["quantity"].round().astype(int)
    work = work[work["quantity"] > 0]
    total_units = int(work["quantity"].sum())
    if total_units > MAX_EXPANDED_UNITS:
        raise IngestError(
            f"Total units ({total_units:,}) exceed the limit of "
            f"{MAX_EXPANDED_UNITS:,}."
        )

    # ── Build items_df: one row per distinct item ──
    agg: dict[str, tuple[str, str]] = {
        "price": ("price", "median"),
        "category": ("category", "first"),
    }
    if "food_cost" in work.columns:
        agg["food_cost"] = ("food_cost", "median")
    if "margin_in" in work.columns:
        agg["margin_in"] = ("margin_in", "median")

    items = work.groupby("item_name", as_index=False).agg(**agg)

    if "food_cost" in items.columns:
        items["food_cost"] = items["food_cost"].fillna(0.0)
        items["margin"] = items["price"] - items["food_cost"]
    elif "margin_in" in items.columns:
        items["food_cost"] = (items["price"] - items["margin_in"]).clip(lower=0.0)
        items["margin"] = items["margin_in"]
    else:
        # No cost/margin in the file: derive from the caller's assumed cost %.
        frac = float(cost_pct) / 100.0
        items["food_cost"] = (items["price"] * frac).round(4)
        items["margin"] = (items["price"] * (1.0 - frac)).round(4)
        warnings.append(
            f"No cost column found; margin derived from an assumed "
            f"{cost_pct:g}% food cost of price (your assumption, not computed)."
        )

    if "margin_in" in items.columns:
        items = items.drop(columns=["margin_in"])

    items = items.reset_index(drop=True)
    items.insert(0, "item_id", range(1, len(items) + 1))
    items = items.rename(columns={"item_name": "name"})
    items = items[["item_id", "name", "price", "food_cost", "category", "margin"]]

    if len(items) < 2:
        raise IngestError(
            "At least 2 distinct menu items are required for a meaningful analysis."
        )

    name_to_id = dict(zip(items["name"], items["item_id"]))

    # ── Build lines_df: one row per sold unit ──
    expanded = work.loc[work.index.repeat(work["quantity"])].copy()
    expanded["item_id"] = expanded["item_name"].map(name_to_id)
    lines = expanded[["order_id", "item_id", "price"]].rename(
        columns={"price": "unit_price"}
    )
    lines = lines.reset_index(drop=True)
    lines.insert(0, "line_id", range(1, len(lines) + 1))

    orders = int(lines["order_id"].nunique())
    if orders < 1:
        raise IngestError("No valid orders found in the file.")

    return IngestResult(
        items_df=items,
        lines_df=lines,
        orders=orders,
        line_items=int(len(lines)),
        distinct_items=int(len(items)),
        warnings=warnings,
    )
