"""Tests for the transaction-upload ingestion pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from analytics.menu_engineering import menu_engineering
from ingest import IngestError, parse_transactions


def _csv(text: str) -> bytes:
    return text.strip().encode("utf-8")


def test_parses_canonical_columns():
    csv = _csv(
        """
order_id,item_name,price,food_cost,category,quantity
1,Burger,10,3,main,2
1,Fries,5,2,side,1
2,Burger,10,3,main,1
2,Soda,3,0.5,drink,3
"""
    )
    result = parse_transactions(csv, "orders.csv")

    assert result.distinct_items == 3
    assert result.orders == 2
    # units: Burger 2+1=3, Fries 1, Soda 3 -> 7 line units
    assert result.line_items == 7

    burger = result.items_df[result.items_df["name"] == "Burger"].iloc[0]
    assert burger["margin"] == pytest.approx(7.0)

    matrix = menu_engineering(result.items_df, result.lines_df)
    assert set(matrix.columns) >= {"item_id", "name", "units_sold", "margin", "quadrant"}
    assert int(matrix[matrix["name"] == "Burger"]["units_sold"].iloc[0]) == 3


def test_maps_synonym_headers():
    csv = _csv(
        """
receipt,product,unit_price,cost
A,Latte,4,1
A,Muffin,3,1
B,Latte,4,1
"""
    )
    result = parse_transactions(csv, "receipts.csv")
    assert result.orders == 2
    assert result.distinct_items == 2


def test_accepts_margin_column_without_food_cost():
    csv = _csv(
        """
order,item,price,margin
1,Tea,3,2
1,Cake,5,3
2,Tea,3,2
"""
    )
    result = parse_transactions(csv, "m.csv")
    tea = result.items_df[result.items_df["name"] == "Tea"].iloc[0]
    assert tea["margin"] == pytest.approx(2.0)
    assert tea["food_cost"] == pytest.approx(1.0)


def test_missing_required_column_raises():
    csv = _csv("item_name,price\nBurger,10\nFries,5")
    with pytest.raises(IngestError):
        parse_transactions(csv, "bad.csv")


def test_missing_cost_and_margin_raises():
    csv = _csv("order_id,item_name,price\n1,Burger,10\n2,Fries,5")
    with pytest.raises(IngestError):
        parse_transactions(csv, "nocost.csv")


def test_cost_pct_derives_margin_without_cost_column():
    csv = _csv(
        """
order_id,item_name,price
1,Burger,10
1,Fries,5
2,Burger,10
"""
    )
    result = parse_transactions(csv, "sales.csv", cost_pct=30)
    burger = result.items_df[result.items_df["name"] == "Burger"].iloc[0]
    assert burger["food_cost"] == pytest.approx(3.0)
    assert burger["margin"] == pytest.approx(7.0)
    assert any("assumed" in w.lower() for w in result.warnings)


def test_cost_column_takes_precedence_over_cost_pct():
    csv = _csv(
        """
order_id,item_name,price,food_cost
1,Burger,10,4
2,Fries,5,2
"""
    )
    result = parse_transactions(csv, "f.csv", cost_pct=90)
    burger = result.items_df[result.items_df["name"] == "Burger"].iloc[0]
    assert burger["margin"] == pytest.approx(6.0)


def test_invalid_cost_pct_raises():
    csv = _csv("order_id,item_name,price\n1,Burger,10\n2,Fries,5")
    with pytest.raises(IngestError):
        parse_transactions(csv, "bad.csv", cost_pct=150)


def test_requires_two_distinct_items():
    csv = _csv("order_id,item_name,price,food_cost\n1,Burger,10,3\n2,Burger,10,3")
    with pytest.raises(IngestError):
        parse_transactions(csv, "single.csv")
