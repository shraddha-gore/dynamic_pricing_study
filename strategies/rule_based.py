import pandas as pd

from config import RULE_PRICE_DECREASE, RULE_PRICE_INCREASE


def _select_candidate_price(candidate_table: pd.DataFrame, target_price: float, base_price: float) -> float:
    ranked = candidate_table.assign(
        distance_to_target=(candidate_table["candidate_price"] - target_price).abs(),
        distance_to_base=(candidate_table["candidate_price"] - base_price).abs(),
    ).sort_values(
        by=["distance_to_target", "distance_to_base", "candidate_price"],
        ascending=[True, True, True],
        kind="mergesort",
    )
    return float(ranked.iloc[0]["candidate_price"])


def choose_price(candidate_table: pd.DataFrame, context: dict) -> float:
    if candidate_table.empty:
        raise ValueError("Rule-based strategy received an empty candidate table.")

    base_price = float(context["base_price"])
    row = context["row"]
    rolling_mean_units = float(row["rolling7_mean_units"])

    base_candidates = candidate_table[candidate_table["candidate_price"] == base_price]
    if base_candidates.empty:
        base_idx = (candidate_table["candidate_price"] - base_price).abs().idxmin()
        base_predicted_demand = float(candidate_table.loc[base_idx, "predicted_demand"])
    else:
        base_predicted_demand = float(base_candidates.iloc[0]["predicted_demand"])

    if base_predicted_demand > rolling_mean_units:
        target_price = base_price * (1.0 + RULE_PRICE_INCREASE)
    elif base_predicted_demand < rolling_mean_units:
        target_price = base_price * (1.0 - RULE_PRICE_DECREASE)
    else:
        target_price = base_price

    return _select_candidate_price(candidate_table, target_price, base_price)
