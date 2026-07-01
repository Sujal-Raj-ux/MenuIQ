"""Menu-engineering (contribution-margin) matrix analytics."""

from __future__ import annotations

from typing import Literal

import pandas as pd

ThresholdMode = Literal["mean", "median"]
Quadrant = Literal["Star", "Plowhorse", "Puzzle", "Dog"]


def _threshold_value(series: pd.Series, mode: ThresholdMode) -> float:
    if mode == "mean":
        return float(series.mean())
    return float(series.median())


def _classify_quadrant(
    above_popularity: bool, above_margin: bool
) -> Quadrant:
    if above_popularity and above_margin:
        return "Star"
    if above_popularity and not above_margin:
        return "Plowhorse"
    if not above_popularity and above_margin:
        return "Puzzle"
    return "Dog"


def menu_engineering(
    items_df: pd.DataFrame,
    lines_df: pd.DataFrame,
    threshold: ThresholdMode = "mean",
) -> pd.DataFrame:
    """
    Build a menu-engineering matrix: popularity (units sold) vs per-unit margin.

    Each item is classified into Star, Plowhorse, Puzzle, or Dog based on whether
    its units sold and margin are above or below the chosen threshold.

    Args:
        items_df: Menu catalog with item_id, name, margin (and related fields).
        lines_df: Order lines with item_id (one row per unit sold).
        threshold: Aggregate used to split high vs low on each axis.
            "mean" is the classic menu-engineering default; "median" is more
            robust when one item dominates volume — borderline items near the
            mean can flip quadrants under median because the cutoff moves.

    Returns:
        DataFrame with one row per item: item_id, name, category, units_sold,
        margin, popularity_threshold, margin_threshold, above_popularity,
        above_margin, quadrant.
    """
    units = (
        lines_df.groupby("item_id")
        .size()
        .rename("units_sold")
        .reset_index()
    )

    result = items_df.merge(units, on="item_id", how="left")
    result["units_sold"] = result["units_sold"].fillna(0).astype(int)
    result["margin"] = pd.to_numeric(result["margin"], errors="coerce")

    pop_cutoff = _threshold_value(result["units_sold"], threshold)
    margin_cutoff = _threshold_value(result["margin"], threshold)

    result["popularity_threshold"] = pop_cutoff
    result["margin_threshold"] = margin_cutoff
    result["above_popularity"] = result["units_sold"] >= pop_cutoff
    result["above_margin"] = result["margin"] >= margin_cutoff
    result["quadrant"] = result.apply(
        lambda row: _classify_quadrant(row["above_popularity"], row["above_margin"]),
        axis=1,
    )

    columns = [
        "item_id",
        "name",
        "category",
        "units_sold",
        "margin",
        "popularity_threshold",
        "margin_threshold",
        "above_popularity",
        "above_margin",
        "quadrant",
    ]
    return result[columns].sort_values("units_sold", ascending=False).reset_index(drop=True)
