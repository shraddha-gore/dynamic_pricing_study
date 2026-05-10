"""
ML pricing strategy.

Greedy revenue maximiser: selects the candidate price with the highest predicted revenue.
Tiebreaks by proximity to the base price, then by price value, to produce deterministic output.
"""

import pandas as pd


def choose_price(candidate_table: pd.DataFrame, context: dict) -> float:
    if candidate_table.empty:
        raise ValueError("ML strategy received an empty candidate table.")

    base_price = float(context["base_price"])
    ranked = candidate_table.assign(
        distance_to_base=(candidate_table["candidate_price"] - base_price).abs()
    ).sort_values(
        by=["predicted_revenue", "distance_to_base", "candidate_price"],
        ascending=[False, True, True],
        kind="mergesort",
    )
    return float(ranked.iloc[0]["candidate_price"])
