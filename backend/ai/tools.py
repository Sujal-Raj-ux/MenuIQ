"""LangChain tools wrapping Phase 2 analytics (curated, no raw SQL)."""

from __future__ import annotations

from langchain_core.tools import StructuredTool

from ai.context import get_active_context
from ai.formatters import (
    format_item_associations,
    format_matrix_facts,
    resolve_item_name,
)


def _get_menu_matrix() -> str:
    """
    Return the full menu-engineering matrix as a compact text summary.

    Each item shows its quadrant (Star/Plowhorse/Puzzle/Dog), units sold,
    and per-unit margin. Use this for overview questions about menu performance.
    """
    matrix_df = get_active_context().matrix_df
    pop_cutoff = float(matrix_df.iloc[0]["popularity_threshold"])
    margin_cutoff = float(matrix_df.iloc[0]["margin_threshold"])
    header = (
        f"Thresholds: popularity >= {pop_cutoff:.0f} units, "
        f"margin >= ${margin_cutoff:.2f}\n"
    )
    return header + format_matrix_facts(matrix_df)


def _get_item_associations(item_name: str) -> str:
    """
    Return top cross-sell associations for a menu item (by name).

    Args:
        item_name: Menu item name, e.g. 'Classic Burger' or 'Onion Rings'.
    """
    ctx = get_active_context()
    items_df = ctx.items_df
    resolved = resolve_item_name(item_name, items_df)
    if resolved is None:
        known = ", ".join(items_df["name"].tolist())
        return f"Unknown item '{item_name}'. Known items: {known}"

    item_id, canonical_name = resolved
    return format_item_associations(
        item_id,
        canonical_name,
        ctx.associations_df,
    )


def _get_item_stats(item_name: str) -> str:
    """
    Return price, popularity, margin, and quadrant stats for one menu item.

    Args:
        item_name: Menu item name, e.g. 'Classic Burger' or 'Onion Rings'.
    """
    ctx = get_active_context()
    items_df = ctx.items_df
    matrix_df = ctx.matrix_df
    resolved = resolve_item_name(item_name, items_df)
    if resolved is None:
        known = ", ".join(items_df["name"].tolist())
        return f"Unknown item '{item_name}'. Known items: {known}"

    item_id, canonical_name = resolved
    row = matrix_df[matrix_df["item_id"] == item_id].iloc[0]
    item_row = items_df[items_df["item_id"] == item_id].iloc[0]
    rank = int(matrix_df.index[matrix_df["item_id"] == item_id][0]) + 1
    total_items = len(matrix_df)

    lines = [
        f"{canonical_name} stats:",
        f"- Price: ${float(item_row['price']):.2f}",
        f"- Quadrant: {row['quadrant']}",
        f"- Units sold: {int(row['units_sold'])} "
        f"(rank {rank}/{total_items} by volume)",
        f"- Per-unit margin: ${float(row['margin']):.2f}",
        f"- Category: {row['category']}",
        f"- Above popularity threshold: {bool(row['above_popularity'])}",
        f"- Above margin threshold: {bool(row['above_margin'])}",
        "",
        format_item_associations(item_id, canonical_name, ctx.associations_df),
    ]
    return "\n".join(lines)


get_menu_matrix = StructuredTool.from_function(
    func=_get_menu_matrix,
    name="get_menu_matrix",
    description=(
        "Get the menu-engineering matrix: every item's quadrant, units sold, "
        "and margin. Use for overview or quadrant questions."
    ),
)

get_item_associations = StructuredTool.from_function(
    func=_get_item_associations,
    name="get_item_associations",
    description=(
        "Get cross-sell associations for one menu item by name. "
        "Shows lift and attach rates for item pairs."
    ),
)

get_item_stats = StructuredTool.from_function(
    func=_get_item_stats,
    name="get_item_stats",
    description=(
        "Get detailed stats for one menu item: price, quadrant, units sold, "
        "margin, rank, and its top associations. Use when asked about a specific item."
    ),
)

ALL_TOOLS = [get_menu_matrix, get_item_associations, get_item_stats]
