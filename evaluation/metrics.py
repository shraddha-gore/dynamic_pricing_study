import json
import logging
from pathlib import Path

import pandas as pd

from config import (
    COL_STOCK_CODE,
    PHASE11_METRIC_COLUMNS,
    PHASE11_PAIRING_KEYS,
    PHASE11_STRATEGY_METRICS_PATH,
    PHASE11_STRATEGY_SUMMARY_PATH,
    PHASE7_STRATEGIES,
    PROJECT_ROOT,
    SIMULATION_RESULTS_PATHS,
)
from preprocessing.common import configured_root
from utils.data_contracts import validate_phase7_results

logger = logging.getLogger(__name__)


def _configured_root_path() -> Path:
    return configured_root(PROJECT_ROOT)


def _results_path(strategy_name: str) -> Path:
    return _configured_root_path() / SIMULATION_RESULTS_PATHS[strategy_name]


def _ensure_required_simulation_outputs() -> None:
    missing_paths = [_results_path(strategy_name) for strategy_name in PHASE7_STRATEGIES if not _results_path(strategy_name).exists()]
    if missing_paths:
        logger.error("Phase 11 evaluation cannot start; missing simulation outputs: %s", missing_paths)
        raise RuntimeError("Missing simulation outputs required for Phase 11 evaluation")


def _validate_result_frame(df: pd.DataFrame, strategy_name: str) -> pd.DataFrame:
    validate_phase7_results(df)

    if not (df["strategy_name"] == strategy_name).all():
        raise ValueError(
            f"Phase 11 evaluation validation failed: strategy_name column does not match '{strategy_name}'."
        )
    if df.duplicated(PHASE11_PAIRING_KEYS).any():
        raise ValueError(
            "Phase 11 evaluation validation failed: duplicate "
            f"({', '.join(PHASE11_PAIRING_KEYS)}) rows found for '{strategy_name}'."
        )

    return df.sort_values(PHASE11_PAIRING_KEYS, kind="mergesort").reset_index(drop=True)


def load_strategy_results() -> dict[str, pd.DataFrame]:
    _ensure_required_simulation_outputs()

    results_by_strategy: dict[str, pd.DataFrame] = {}
    for strategy_name in PHASE7_STRATEGIES:
        result_path = _results_path(strategy_name)
        logger.info("Loading Phase 7 simulation results for strategy: %s from %s", strategy_name, result_path)
        result_df = pd.read_parquet(result_path)
        results_by_strategy[strategy_name] = _validate_result_frame(result_df, strategy_name)

    return results_by_strategy


def _compute_product_metrics(all_results_df: pd.DataFrame) -> pd.DataFrame:
    grouped = all_results_df.groupby(["strategy_name", COL_STOCK_CODE], sort=True)
    product_metrics = grouped.agg(
        total_revenue=("predicted_revenue", "sum"),
        mean_daily_revenue=("predicted_revenue", "mean"),
        mean_absolute_change=("abs_price_change", "mean"),
        max_price_jump=("abs_price_change", "max"),
        change_frequency=("price_change", lambda series: float(series.ne(0).mean())),
    ).reset_index()

    price_std = grouped["chosen_price"].std(ddof=0).reset_index(name="price_std")
    product_metrics = product_metrics.merge(price_std, on=["strategy_name", COL_STOCK_CODE], how="inner")
    product_metrics = product_metrics.rename(columns={"strategy_name": "strategy"})
    product_metrics["metric_level"] = "product"
    return product_metrics[PHASE11_METRIC_COLUMNS]


def _compute_strategy_metrics(product_metrics_df: pd.DataFrame) -> pd.DataFrame:
    strategy_metrics = product_metrics_df.groupby("strategy", sort=True).agg(
        total_revenue=("total_revenue", "sum"),
        mean_daily_revenue=("mean_daily_revenue", "mean"),
        mean_absolute_change=("mean_absolute_change", "mean"),
        price_std=("price_std", "mean"),
        max_price_jump=("max_price_jump", "max"),
        change_frequency=("change_frequency", "mean"),
    ).reset_index()
    strategy_metrics[COL_STOCK_CODE] = "ALL"
    strategy_metrics["metric_level"] = "strategy"
    return strategy_metrics[PHASE11_METRIC_COLUMNS]


def _build_summary(strategy_metrics_df: pd.DataFrame) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    summary_columns = [
        column
        for column in PHASE11_METRIC_COLUMNS
        if column not in {COL_STOCK_CODE, "strategy", "metric_level"}
    ]
    for row in strategy_metrics_df.to_dict(orient="records"):
        strategy_name = str(row["strategy"])
        summary[strategy_name] = {column: float(row[column]) for column in summary_columns}
    return summary


def compute_metrics() -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    logger.info("Phase 11 metrics computation started.")
    results_by_strategy = load_strategy_results()
    all_results_df = pd.concat(results_by_strategy.values(), ignore_index=True)

    product_metrics_df = _compute_product_metrics(all_results_df)
    strategy_metrics_df = _compute_strategy_metrics(product_metrics_df)
    combined_metrics_df = pd.concat([product_metrics_df, strategy_metrics_df], ignore_index=True)
    combined_metrics_df = combined_metrics_df.sort_values(["metric_level", "strategy", COL_STOCK_CODE], kind="mergesort")
    combined_metrics_df = combined_metrics_df.reset_index(drop=True)

    summary = _build_summary(strategy_metrics_df)

    root_path = _configured_root_path()
    metrics_output_path = root_path / PHASE11_STRATEGY_METRICS_PATH
    summary_output_path = root_path / PHASE11_STRATEGY_SUMMARY_PATH
    metrics_output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_output_path.parent.mkdir(parents=True, exist_ok=True)

    combined_metrics_df.to_parquet(metrics_output_path, index=False)
    summary_output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    logger.info(
        "Phase 11 metrics written successfully. Rows: %s | Metrics path: %s | Summary path: %s",
        len(combined_metrics_df),
        metrics_output_path,
        summary_output_path,
    )
    return combined_metrics_df, summary
