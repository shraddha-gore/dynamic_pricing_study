import pandas as pd

from config import HYBRID_SMOOTHING_ALPHA, MAX_DAILY_CHANGE


def _select_ml_optimal_price(candidate_table: pd.DataFrame, base_price: float) -> float:
    ranked = candidate_table.assign(
        distance_to_base=(candidate_table["candidate_price"] - base_price).abs()
    ).sort_values(
        by=["predicted_revenue", "distance_to_base", "candidate_price"],
        ascending=[False, True, True],
        kind="mergesort",
    )
    return float(ranked.iloc[0]["candidate_price"])


def choose_price(candidate_table: pd.DataFrame, context: dict) -> float:
    if candidate_table.empty:
        raise ValueError("Hybrid strategy received an empty candidate table.")

    base_price = float(context["base_price"])
    previous_price = float(context["previous_price"])

    ml_price = _select_ml_optimal_price(candidate_table, base_price)

    lower_bound = previous_price * (1.0 - MAX_DAILY_CHANGE)
    upper_bound = previous_price * (1.0 + MAX_DAILY_CHANGE)
    clamped_price = min(max(ml_price, lower_bound), upper_bound)

    smoothed_price = (HYBRID_SMOOTHING_ALPHA * clamped_price) + (
        (1.0 - HYBRID_SMOOTHING_ALPHA) * previous_price
    )

    ranked = candidate_table.assign(
        distance_to_smoothed=(candidate_table["candidate_price"] - smoothed_price).abs(),
        distance_to_base=(candidate_table["candidate_price"] - base_price).abs(),
    ).sort_values(
        by=["distance_to_smoothed", "distance_to_base", "candidate_price"],
        ascending=[True, True, True],
        kind="mergesort",
    )
    return float(ranked.iloc[0]["candidate_price"])
