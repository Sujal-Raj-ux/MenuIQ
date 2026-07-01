"""Validate analytics against the planted Phase 1 answer key."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from analytics.market_basket import market_basket
from analytics.menu_engineering import menu_engineering
from db import load_transaction_data


@pytest.fixture(scope="module")
def frames():
    items_df, _orders_df, lines_df = load_transaction_data()
    return items_df, lines_df


def test_lobster_roll_to_onion_rings_lift(frames):
    """Planted pattern: Lobster Roll (3) -> Onion Rings (4), lift ~ 6.3."""
    items_df, lines_df = frames
    associations = market_basket(lines_df, items_df=items_df)

    pair = associations[
        (associations["antecedent_id"] == 3) & (associations["consequent_id"] == 4)
    ]
    assert not pair.empty, "Expected Lobster Roll -> Onion Rings association"

    lift = float(pair.iloc[0]["lift"])
    assert 6.0 <= lift <= 6.6, f"Expected lift ~6.3, got {lift:.2f}"


def test_classic_burger_is_star(frames):
    """Planted pattern: Classic Burger classifies as Star at mean threshold."""
    items_df, lines_df = frames
    matrix = menu_engineering(items_df, lines_df, threshold="mean")

    burger = matrix[matrix["item_id"] == 1]
    assert not burger.empty
    assert burger.iloc[0]["quadrant"] == "Star"


def test_expected_quadrants_at_mean_threshold(frames):
    """Full quadrant answer key using mean thresholds."""
    items_df, lines_df = frames
    matrix = menu_engineering(items_df, lines_df, threshold="mean")
    expected = {
        1: "Star",        # Classic Burger
        2: "Plowhorse",   # Truffle Fries
        3: "Puzzle",      # Lobster Roll
        4: "Dog",         # Onion Rings
        5: "Puzzle",      # Veggie Burger
        6: "Plowhorse",   # Soda
        7: "Dog",         # Milkshake
    }

    for item_id, quadrant in expected.items():
        actual = matrix.loc[matrix["item_id"] == item_id, "quadrant"].iloc[0]
        name = matrix.loc[matrix["item_id"] == item_id, "name"].iloc[0]
        assert actual == quadrant, f"{name} (id={item_id}): expected {quadrant}, got {actual}"


def test_burger_to_truffle_fries_strong_attach(frames):
    """Planted pattern: Classic Burger -> Truffle Fries ~70% attach rate."""
    items_df, lines_df = frames
    associations = market_basket(lines_df, items_df=items_df)

    pair = associations[
        (associations["antecedent_id"] == 1) & (associations["consequent_id"] == 2)
    ]
    assert not pair.empty

    confidence = float(pair.iloc[0]["confidence"])
    assert confidence >= 0.65, f"Expected ~70% attach rate, got {confidence:.2%}"
