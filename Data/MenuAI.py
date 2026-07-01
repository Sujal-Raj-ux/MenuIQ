"""
MenuIQ - synthetic data generator (Phase 1, Step 1)

Generates two CSV files that imitate a small restaurant's point-of-sale history:
  - menu_items.csv : one row per menu item (price + food cost)
  - order_lines.csv: one row per item sold (the "receipts")

The data has DELIBERATELY PLANTED patterns so that later, when you build the
analytics engine, you have a ground truth to check it against. If your basket
analysis doesn't rediscover these patterns, your CODE is wrong - not the data.

Stdlib only. No pip install needed.  Run:  python generate_data.py
"""

import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)  # reproducible: same data every run, so your validation is repeatable

N_ORDERS = 2000
DAYS_OF_HISTORY = 90
START_DATE = datetime(2025, 1, 1, 11, 0, 0)

# item_id: (name, price, food_cost, category, anchor_weight)
# anchor_weight = how often this item is the FIRST thing chosen in an order.
MENU = {
    1: ("Classic Burger", 10.00, 3.00, "main",  50),
    2: ("Truffle Fries",   6.00, 1.50, "side",  15),
    3: ("Lobster Roll",   18.00, 9.00, "main",   8),
    4: ("Onion Rings",     5.00, 2.00, "side",   6),
    5: ("Veggie Burger",  11.00, 4.00, "main",  18),
    6: ("Soda",            3.00, 0.50, "drink", 30),
    7: ("Milkshake",       7.00, 2.50, "drink", 12),
}

# planted cross-sell rules: if `src` is in the basket, add `dst` with probability p
ATTACH_RULES = [
    (1, 2, 0.70),  # Classic Burger -> Truffle Fries 70%   (strong, common pair)
    (3, 4, 0.75),  # Lobster Roll   -> Onion Rings   75%   (the "hidden gem" high-lift pair)
    (5, 7, 0.25),  # Veggie Burger  -> Milkshake     25%
]
SODA_ATTACH_P = 0.50   # any order with a main -> add Soda 50%
RANDOM_EXTRA_P = 0.10  # 10% of orders get one extra random item (noise)


def weighted_anchor():
    """Pick the first item of an order, biased by popularity weight."""
    ids = list(MENU.keys())
    weights = [MENU[i][4] for i in ids]
    return random.choices(ids, weights=weights, k=1)[0]


def build_order():
    """Build one basket: an anchor item plus planted attachments."""
    basket = {weighted_anchor()}
    for src, dst, p in ATTACH_RULES:
        if src in basket and random.random() < p:
            basket.add(dst)
    if any(MENU[i][3] == "main" for i in basket) and random.random() < SODA_ATTACH_P:
        basket.add(6)  # Soda
    if random.random() < RANDOM_EXTRA_P:
        basket.add(random.choice(list(MENU.keys())))
    return basket


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(out_dir, "menu_items.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "name", "price", "food_cost", "category"])
        for i, (name, price, cost, cat, _) in MENU.items():
            w.writerow([i, name, f"{price:.2f}", f"{cost:.2f}", cat])

    rows = []
    for order_id in range(1001, 1001 + N_ORDERS):
        ts = START_DATE + timedelta(minutes=random.randint(0, DAYS_OF_HISTORY * 24 * 60))
        for item_id in build_order():
            name, price, *_ = MENU[item_id]
            rows.append([order_id, item_id, name, f"{price:.2f}", ts.isoformat(sep=" ")])

    with open(os.path.join(out_dir, "order_lines.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "item_id", "item_name", "price", "ordered_at"])
        w.writerows(rows)

    print_ground_truth(rows)


def print_ground_truth(rows):
    """Print the answer key: what your Phase 2 analytics SHOULD rediscover."""
    from collections import Counter, defaultdict
    units = Counter(r[2] for r in rows)
    baskets = defaultdict(set)
    for order_id, item_id, name, *_ in rows:
        baskets[order_id].add(name)

    print(f"Generated {len(baskets)} orders, {len(rows)} order lines.\n")
    print("UNITS SOLD per item (this is your popularity ranking):")
    for name, n in units.most_common():
        print(f"  {name:<16} {n}")

    total = len(baskets)
    lob = sum(1 for b in baskets.values() if "Lobster Roll" in b)
    onion = sum(1 for b in baskets.values() if "Onion Rings" in b)
    both = sum(1 for b in baskets.values() if {"Lobster Roll", "Onion Rings"} <= b)
    p_onion = onion / total
    p_onion_given_lob = both / lob if lob else 0
    lift = p_onion_given_lob / p_onion if p_onion else 0
    print("\nPLANTED PATTERN CHECK  (Lobster Roll -> Onion Rings):")
    print(f"  P(onion)            = {p_onion:.3f}")
    print(f"  P(onion | lobster)  = {p_onion_given_lob:.3f}")
    print(f"  lift                = {lift:.1f}x   (well above 1 = a real, strong pairing)")


if __name__ == "__main__":
    main()