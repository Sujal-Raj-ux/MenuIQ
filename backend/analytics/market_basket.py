"""Market-basket / association-rule mining analytics."""

from __future__ import annotations

import pandas as pd


def market_basket(
    lines_df: pd.DataFrame,
    items_df: pd.DataFrame | None = None,
    min_support: float = 0.01,
    min_lift: float = 1.0,
) -> pd.DataFrame:
    """
    Compute association metrics for every directed item pair (A -> B).

    Metrics (computed over distinct orders):
        support(A, B)  = P(A and B)
        confidence(A -> B) = P(B | A)
        lift(A -> B) = confidence(A -> B) / P(B)

    Args:
        lines_df: Order lines with order_id and item_id.
        items_df: Optional menu catalog; when provided, item names are attached.
        min_support: Minimum support to include a pair in the result.
        min_lift: Minimum lift to include a pair in the result.

    Returns:
        DataFrame sorted by lift descending with columns:
        antecedent_id, consequent_id, (optional names), support, confidence, lift.
    """
    baskets = (
        lines_df.groupby("order_id")["item_id"]
        .apply(lambda ids: set(ids.tolist()))
        .tolist()
    )
    total_orders = len(baskets)
    if total_orders == 0:
        return pd.DataFrame(
            columns=[
                "antecedent_id",
                "consequent_id",
                "support",
                "confidence",
                "lift",
            ]
        )

    item_ids = sorted(lines_df["item_id"].unique())
    order_count: dict[int, int] = {item_id: 0 for item_id in item_ids}
    pair_count: dict[tuple[int, int], int] = {}

    for basket in baskets:
        for item_id in basket:
            order_count[item_id] += 1
        for antecedent in basket:
            for consequent in basket:
                if antecedent == consequent:
                    continue
                key = (antecedent, consequent)
                pair_count[key] = pair_count.get(key, 0) + 1

    rows: list[dict[str, float | int]] = []
    for (antecedent_id, consequent_id), both_count in pair_count.items():
        support = both_count / total_orders
        if support < min_support:
            continue

        antecedent_orders = order_count[antecedent_id]
        consequent_orders = order_count[consequent_id]
        if antecedent_orders == 0 or consequent_orders == 0:
            continue

        confidence = both_count / antecedent_orders
        consequent_support = consequent_orders / total_orders
        lift = confidence / consequent_support if consequent_support > 0 else 0.0

        if lift < min_lift:
            continue

        rows.append(
            {
                "antecedent_id": antecedent_id,
                "consequent_id": consequent_id,
                "support": round(support, 6),
                "confidence": round(confidence, 6),
                "lift": round(lift, 6),
            }
        )

    columns = [
        "antecedent_id",
        "consequent_id",
        "support",
        "confidence",
        "lift",
    ]
    result = pd.DataFrame(rows, columns=columns)
    if result.empty:
        return result

    if items_df is not None:
        names = items_df.set_index("item_id")["name"]
        result["antecedent_name"] = result["antecedent_id"].map(names)
        result["consequent_name"] = result["consequent_id"].map(names)

    return result.sort_values("lift", ascending=False).reset_index(drop=True)
