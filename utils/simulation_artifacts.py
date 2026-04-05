import logging
from pathlib import Path

import pandas as pd

from config import EVALUATION_PAIRING_KEYS, SIMULATION_STRATEGIES, PROJECT_ROOT, SIMULATION_RESULTS_PATHS
from preprocessing.common import configured_path_from_map
from utils.data_contracts import validate_simulation_results

logger = logging.getLogger(__name__)


def simulation_result_path(strategy_name: str) -> Path:
    return configured_path_from_map(PROJECT_ROOT, SIMULATION_RESULTS_PATHS, strategy_name)


def ensure_required_simulation_outputs() -> None:
    missing_paths = [simulation_result_path(strategy_name) for strategy_name in SIMULATION_STRATEGIES if not simulation_result_path(strategy_name).exists()]
    if missing_paths:
        logger.error("Evaluation cannot start; missing simulation outputs: %s", missing_paths)
        raise RuntimeError("Missing simulation outputs required for Evaluation")


def validate_strategy_results(df: pd.DataFrame, strategy_name: str) -> pd.DataFrame:
    validate_simulation_results(df)

    if not (df["strategy_name"] == strategy_name).all():
        raise ValueError(
            f"Evaluation validation failed: strategy_name column does not match '{strategy_name}'."
        )
    if df.duplicated(EVALUATION_PAIRING_KEYS).any():
        raise ValueError(
            "Evaluation validation failed: duplicate "
            f"({', '.join(EVALUATION_PAIRING_KEYS)}) rows found for '{strategy_name}'."
        )

    return df.sort_values(EVALUATION_PAIRING_KEYS, kind="mergesort").reset_index(drop=True)


def load_strategy_results() -> dict[str, pd.DataFrame]:
    ensure_required_simulation_outputs()

    results_by_strategy: dict[str, pd.DataFrame] = {}
    for strategy_name in SIMULATION_STRATEGIES:
        result_path = simulation_result_path(strategy_name)
        logger.info("Loading Simulation results for strategy: %s from %s", strategy_name, result_path)
        result_df = pd.read_parquet(result_path)
        results_by_strategy[strategy_name] = validate_strategy_results(result_df, strategy_name)

    return results_by_strategy
