"""Helpers for turning analytics DataFrames into LLM-safe fact blocks."""

from __future__ import annotations

import pandas as pd


def resolve_item_name(name: str, items_df: pd.DataFrame) -> tuple[int, str] | None:
    """Match a user-supplied item name to catalog row (case-insensitive)."""
    query = name.strip().lower()
    if not query:
        return None

    exact = items_df[items_df["name"].str.lower() == query]
    if len(exact) == 1:
        row = exact.iloc[0]
        return int(row["item_id"]), str(row["name"])

    partial = items_df[items_df["name"].str.lower().str.contains(query, regex=False)]
    if len(partial) == 1:
        row = partial.iloc[0]
        return int(row["item_id"]), str(row["name"])

    return None


def format_matrix_facts(matrix_df: pd.DataFrame) -> str:
    """Compact menu-engineering summary for LLM prompts and tools."""
    lines = ["Menu-engineering matrix (mean thresholds):"]
    for _, row in matrix_df.iterrows():
        lines.append(
            f"- {row['name']} ({row['quadrant']}): "
            f"{int(row['units_sold'])} units sold, ${float(row['margin']):.2f} margin, "
            f"category={row['category']}"
        )
    return "\n".join(lines)


def format_top_associations(associations_df: pd.DataFrame, limit: int = 8) -> str:
    """Top association pairs by lift for LLM prompts."""
    if associations_df.empty:
        return "No association pairs met the support/lift thresholds."

    lines = [f"Top {min(limit, len(associations_df))} item associations by lift:"]
    for _, row in associations_df.head(limit).iterrows():
        lines.append(
            f"- {row['antecedent_name']} -> {row['consequent_name']}: "
            f"lift={float(row['lift']):.2f}, "
            f"confidence={float(row['confidence']):.1%}, "
            f"support={float(row['support']):.3f}"
        )
    return "\n".join(lines)


def format_item_associations(
    item_id: int,
    item_name: str,
    associations_df: pd.DataFrame,
    limit: int = 5,
) -> str:
    """Associations where the item is antecedent or consequent."""
    required = {"antecedent_id", "consequent_id"}
    if associations_df.empty or not required.issubset(associations_df.columns):
        return "\n".join(
            [
                f"Associations for {item_name}:",
                "- No strong pairings found at current thresholds.",
            ]
        )

    as_source = associations_df[associations_df["antecedent_id"] == item_id].head(limit)
    as_target = associations_df[associations_df["consequent_id"] == item_id].head(limit)

    lines = [f"Associations for {item_name}:"]

    if as_source.empty and as_target.empty:
        lines.append("- No strong pairings found at current thresholds.")
        return "\n".join(lines)

    if not as_source.empty:
        lines.append("When customers order this item, they also tend to add:")
        for _, row in as_source.iterrows():
            lines.append(
                f"  -> {row['consequent_name']}: lift={float(row['lift']):.2f}, "
                f"attach rate={float(row['confidence']):.1%}"
            )

    if not as_target.empty:
        lines.append("Often ordered alongside (this item is the add-on):")
        for _, row in as_target.iterrows():
            lines.append(
                f"  <- {row['antecedent_name']}: lift={float(row['lift']):.2f}, "
                f"attach rate={float(row['confidence']):.1%}"
            )

    return "\n".join(lines)
