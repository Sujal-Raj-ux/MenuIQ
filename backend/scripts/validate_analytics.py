#!/usr/bin/env python3
"""Run planted-pattern checks against live Postgres data (Phase 2 answer key)."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from analytics.market_basket import market_basket
from analytics.menu_engineering import menu_engineering
from db import load_transaction_data


def main() -> None:
    items_df, _orders_df, lines_df = load_transaction_data()

    matrix = menu_engineering(items_df, lines_df, threshold="mean")
    associations = market_basket(lines_df, items_df=items_df)

    lobster_onion = associations[
        (associations["antecedent_id"] == 3) & (associations["consequent_id"] == 4)
    ].iloc[0]

    burger_quadrant = matrix.loc[matrix["item_id"] == 1, "quadrant"].iloc[0]

    print("Menu-engineering matrix (mean thresholds):")
    print(matrix[["name", "units_sold", "margin", "quadrant"]].to_string(index=False))
    print()
    print(f"Classic Burger quadrant: {burger_quadrant}  (expected: Star)")
    print(
        f"Lobster Roll -> Onion Rings lift: {lobster_onion['lift']:.2f}  "
        f"(expected: 6.3 ± 0.3)"
    )

    lift_ok = 6.0 <= float(lobster_onion["lift"]) <= 6.6
    star_ok = burger_quadrant == "Star"
    if lift_ok and star_ok:
        print("\nValidation PASSED.")
        sys.exit(0)

    print("\nValidation FAILED.")
    sys.exit(1)


if __name__ == "__main__":
    main()
