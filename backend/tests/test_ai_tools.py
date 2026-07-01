"""Tests for AI tools (no OpenAI API key required)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ai.context import AnalyticsContext
from ai.formatters import format_item_associations, resolve_item_name
from ai.tools import _get_item_associations, _get_item_stats, _get_menu_matrix


@pytest.fixture(scope="module")
def ctx():
    return AnalyticsContext()


def test_get_menu_matrix_lists_all_quadrants(ctx):
    text = _get_menu_matrix()
    for quadrant in ("Star", "Plowhorse", "Puzzle", "Dog"):
        assert quadrant in text
    assert "Classic Burger" in text
    assert "units sold" in text


def test_get_item_stats_onion_rings_is_dog(ctx):
    text = _get_item_stats("Onion Rings")
    assert "Quadrant: Dog" in text
    assert "Units sold: 213" in text


def test_get_item_stats_includes_price(ctx):
    text = _get_item_stats("Classic Burger")
    assert "Price: $10.00" in text


def test_get_item_associations_lobster_to_onion(ctx):
    text = _get_item_associations("Lobster Roll")
    assert "Onion Rings" in text
    assert "lift=" in text


def test_format_item_associations_handles_empty_frame():
    text = format_item_associations(1, "Burger", pd.DataFrame())
    assert "No strong pairings found" in text


def test_resolve_item_name_partial_match(ctx):
    resolved = resolve_item_name("lobster", ctx.items_df)
    assert resolved is not None
    _item_id, name = resolved
    assert name == "Lobster Roll"


def test_unknown_item_returns_helpful_message(ctx):
    text = _get_item_stats("Pizza")
    assert "Unknown item" in text
    assert "Classic Burger" in text
