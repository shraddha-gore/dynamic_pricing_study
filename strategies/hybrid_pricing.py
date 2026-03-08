import pandas as pd

from config import HYBRID_SMOOTHING_ALPHA, MAX_DAILY_CHANGE


def choose_price(candidate_table: pd.DataFrame, context: dict) -> float:
    if candidate_table.empty:
        raise ValueError("Hybrid strategy received an empty candidate table.")

    base_price = float(context["base_price"])

    ml_best_idx = candidate_table["predicted_revenue"].idxmax()
    ml_price = float(candidate_table.loc[ml_best_idx, "candidate_price"])

    lower_bound = base_price * (1.0 - MAX_DAILY_CHANGE)
    upper_bound = base_price * (1.0 + MAX_DAILY_CHANGE)
    clamped_price = min(max(ml_price, lower_bound), upper_bound)

    smoothed_price = (HYBRID_SMOOTHING_ALPHA * clamped_price) + ((1.0 - HYBRID_SMOOTHING_ALPHA) * base_price)

    nearest_idx = (candidate_table["candidate_price"] - smoothed_price).abs().idxmin()
    return float(candidate_table.loc[nearest_idx, "candidate_price"])
