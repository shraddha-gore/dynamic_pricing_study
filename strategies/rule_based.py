import pandas as pd


RULE_ADJUSTMENT_PCT = 0.02


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
        target_price = base_price * (1.0 + RULE_ADJUSTMENT_PCT)
    elif base_predicted_demand < rolling_mean_units:
        target_price = base_price * (1.0 - RULE_ADJUSTMENT_PCT)
    else:
        target_price = base_price

    nearest_idx = (candidate_table["candidate_price"] - target_price).abs().idxmin()
    return float(candidate_table.loc[nearest_idx, "candidate_price"])
