import logging
from pathlib import Path
import sys
from typing import Callable

import joblib
import numpy as np
import pandas as pd

# Ensure project-root imports work when executing this file directly.
PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from config import (
    COL_STOCK_CODE,
    FEATURE_TEST_DATA_PATH,
    PHASE6_FEATURE_COLUMNS,
    PHASE6_MODEL_ARTIFACT_PATH,
    PHASE7_CANDIDATE_FROZEN_COLUMNS,
    PHASE7_GRID_POINTS,
    PHASE7_RESULT_FROZEN_COLUMNS,
    PHASE7_STRATEGIES,
    PRICE_GRID_PERCENTAGE,
    PROJECT_ROOT,
    SIMULATION_CANDIDATE_PATHS,
    SIMULATION_RESULTS_PATHS,
)
from preprocessing.common import configured_root, ensure_required_columns
from strategies.hybrid_pricing import choose_price as choose_hybrid_price
from strategies.ml_pricing import choose_price as choose_ml_price
from strategies.rule_based import choose_price as choose_rule_price
from utils.data_contracts import validate_phase7_candidates, validate_phase7_results

logger = logging.getLogger(__name__)

CONFIGURED_ROOT_PATH = configured_root(PROJECT_ROOT)
TEST_INPUT_PATH = CONFIGURED_ROOT_PATH / FEATURE_TEST_DATA_PATH
MODEL_INPUT_PATH = CONFIGURED_ROOT_PATH / PHASE6_MODEL_ARTIFACT_PATH

StrategySelector = Callable[[pd.DataFrame, dict], float]
STRATEGY_SELECTORS: dict[str, StrategySelector] = {
    "rule": choose_rule_price,
    "ml": choose_ml_price,
    "hybrid": choose_hybrid_price,
}


def _generate_candidate_prices(base_price: float) -> np.ndarray:
    low = base_price * (1.0 - PRICE_GRID_PERCENTAGE)
    high = base_price * (1.0 + PRICE_GRID_PERCENTAGE)
    return np.linspace(low, high, PHASE7_GRID_POINTS, dtype=float)


def _build_candidates_for_row(row: pd.Series, model) -> pd.DataFrame:
    base_price = float(row["avg_daily_price"])
    candidate_prices = _generate_candidate_prices(base_price)
    feature_rows: list[dict[str, float]] = []

    for candidate_price in candidate_prices:
        feature_row = {feature: float(row[feature]) for feature in PHASE6_FEATURE_COLUMNS}
        feature_row["avg_daily_price"] = float(candidate_price)
        feature_rows.append(feature_row)

    feature_df = pd.DataFrame(feature_rows, columns=PHASE6_FEATURE_COLUMNS)
    predicted_demand = np.clip(model.predict(feature_df).astype(float), a_min=0.0, a_max=None)
    predicted_revenue = candidate_prices * predicted_demand

    candidates_df = pd.DataFrame(
        {
            "invoice_day": [row["invoice_day"]] * len(candidate_prices),
            COL_STOCK_CODE: [row[COL_STOCK_CODE]] * len(candidate_prices),
            "candidate_price": candidate_prices,
            "predicted_demand": predicted_demand,
            "predicted_revenue": predicted_revenue,
        }
    )
    candidates_df["candidate_rank_by_revenue"] = (
        candidates_df["predicted_revenue"].rank(ascending=False, method="first").astype("int64")
    )
    candidates_df = candidates_df.sort_values("candidate_price", kind="mergesort").reset_index(drop=True)
    return candidates_df


def _build_simulation_outputs(test_df: pd.DataFrame, model, strategy_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    selector = STRATEGY_SELECTORS[strategy_name]

    all_candidates: list[pd.DataFrame] = []
    all_results: list[dict[str, object]] = []
    previous_price_by_product: dict[str, float] = {}

    for _, row in test_df.iterrows():
        candidates_df = _build_candidates_for_row(row, model)
        validate_phase7_candidates(candidates_df[PHASE7_CANDIDATE_FROZEN_COLUMNS])

        base_price = float(row["avg_daily_price"])
        stock_code = str(row[COL_STOCK_CODE])
        previous_price = previous_price_by_product.get(stock_code, base_price)
        context = {"base_price": base_price, "row": row, "strategy_name": strategy_name}
        if strategy_name == "hybrid":
            context["previous_price"] = previous_price
        required_context_keys = {"base_price", "row", "strategy_name"} | (
            {"previous_price"} if strategy_name == "hybrid" else set()
        )
        if set(context.keys()) != required_context_keys:
            raise ValueError(
                "Strategy context validation failed: expected keys "
                f"{sorted(required_context_keys)}, got {sorted(context.keys())}."
            )
        chosen_price = float(selector(candidates_df.copy(), context))

        chosen_rows = candidates_df[candidates_df["candidate_price"] == chosen_price]
        if chosen_rows.empty:
            nearest_idx = (candidates_df["candidate_price"] - chosen_price).abs().idxmin()
            chosen_row = candidates_df.loc[nearest_idx]
            chosen_price = float(chosen_row["candidate_price"])
        else:
            chosen_row = chosen_rows.iloc[0]

        price_change = chosen_price - previous_price
        previous_price_by_product[stock_code] = chosen_price

        all_candidates.append(candidates_df)
        all_results.append(
            {
                "invoice_day": row["invoice_day"],
                COL_STOCK_CODE: stock_code,
                "base_price": base_price,
                "previous_price": previous_price,
                "chosen_price": chosen_price,
                "price_change": price_change,
                "abs_price_change": abs(price_change),
                "predicted_demand": float(chosen_row["predicted_demand"]),
                "predicted_revenue": float(chosen_row["predicted_revenue"]),
                "strategy_name": strategy_name,
            }
        )

    candidates_output = pd.concat(all_candidates, ignore_index=True)
    candidates_output = candidates_output[PHASE7_CANDIDATE_FROZEN_COLUMNS]
    results_output = pd.DataFrame(all_results, columns=PHASE7_RESULT_FROZEN_COLUMNS)
    return candidates_output, results_output


def run_phase7(strategy_name: str) -> None:
    if strategy_name not in PHASE7_STRATEGIES:
        raise ValueError(f"Unsupported strategy for Phase 7 simulation: {strategy_name}")

    logger.info("Phase 7 simulation started for strategy: %s", strategy_name)
    if not TEST_INPUT_PATH.exists():
        raise FileNotFoundError(f"Phase 7 test dataset not found: {TEST_INPUT_PATH}")
    if not MODEL_INPUT_PATH.exists():
        raise FileNotFoundError(f"Phase 7 model artifact not found: {MODEL_INPUT_PATH}")

    test_df = pd.read_parquet(TEST_INPUT_PATH)
    ensure_required_columns(
        test_df,
        ["invoice_day", COL_STOCK_CODE, "avg_daily_price", *PHASE6_FEATURE_COLUMNS],
        "Phase 7 simulation input",
    )
    test_df = test_df.sort_values([COL_STOCK_CODE, "invoice_day"], kind="mergesort").reset_index(drop=True)

    model = joblib.load(MODEL_INPUT_PATH)
    candidates_df, results_df = _build_simulation_outputs(test_df, model, strategy_name)

    validate_phase7_candidates(candidates_df)
    validate_phase7_results(results_df)

    candidates_output_path = CONFIGURED_ROOT_PATH / SIMULATION_CANDIDATE_PATHS[strategy_name]
    results_output_path = CONFIGURED_ROOT_PATH / SIMULATION_RESULTS_PATHS[strategy_name]
    candidates_output_path.parent.mkdir(parents=True, exist_ok=True)
    results_output_path.parent.mkdir(parents=True, exist_ok=True)

    candidates_df.to_parquet(candidates_output_path, index=False)
    results_df.to_parquet(results_output_path, index=False)

    logger.info(
        (
            "Phase 7 summary | strategy: %s | test rows: %s | candidate rows: %s | "
            "result rows: %s | candidate output: %s | result output: %s"
        ),
        strategy_name,
        len(test_df),
        len(candidates_df),
        len(results_df),
        candidates_output_path,
        results_output_path,
    )
    logger.info("Phase 7 simulation completed successfully for strategy: %s", strategy_name)


if __name__ == "__main__":
    raise SystemExit("Phase 7 requires an explicit strategy. Use main.py --simulate {rule|ml|hybrid}.")
