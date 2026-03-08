import pandas as pd


def choose_price(candidate_table: pd.DataFrame, context: dict) -> float:
    if candidate_table.empty:
        raise ValueError("ML strategy received an empty candidate table.")

    best_idx = candidate_table["predicted_revenue"].idxmax()
    return float(candidate_table.loc[best_idx, "candidate_price"])
