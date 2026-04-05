import json
import logging
from collections.abc import Callable

import pandas as pd

from config import (
    COL_STOCK_CODE,
    EVALUATION_METRIC_COLUMNS,
    EVALUATION_PRODUCT_METRIC_LEVEL,
    EVALUATION_STRATEGY_METRIC_LEVEL,
    EVALUATION_SUMMARY_STOCK_CODE,
    EVALUATION_STRATEGY_METRICS_PATH,
    EVALUATION_STRATEGY_SUMMARY_PATH,
    PROJECT_ROOT,
)
from preprocessing.common import configured_path
from utils.simulation_artifacts import load_strategy_results

logger = logging.getLogger(__name__)


def _summary_metric_columns() -> list[str]:
    return [
        column
        for column in EVALUATION_METRIC_COLUMNS
        if column not in {COL_STOCK_CODE, "strategy", "metric_level"}
    ]


def _product_metric_aggregations() -> dict[str, tuple[str, str | Callable[[pd.Series], float]]]:
    return {
        "total_revenue": ("predicted_revenue", "sum"),
        "mean_daily_revenue": ("predicted_revenue", "mean"),
        "mean_absolute_change": ("abs_price_change", "mean"),
        "max_price_jump": ("abs_price_change", "max"),
        "change_frequency": ("price_change", lambda series: float(series.ne(0).mean())),
    }


def _strategy_metric_aggregations() -> dict[str, tuple[str, str]]:
    return {
        "total_revenue": ("total_revenue", "sum"),
        "mean_daily_revenue": ("mean_daily_revenue", "mean"),
        "mean_absolute_change": ("mean_absolute_change", "mean"),
        "price_std": ("price_std", "mean"),
        "max_price_jump": ("max_price_jump", "max"),
        "change_frequency": ("change_frequency", "mean"),
    }


def _finalise_metrics_frame(metrics_df: pd.DataFrame, metric_level: str) -> pd.DataFrame:
    finalised_df = metrics_df.copy()
    finalised_df["metric_level"] = metric_level
    return finalised_df[EVALUATION_METRIC_COLUMNS]


def _compute_product_metrics(all_results_df: pd.DataFrame) -> pd.DataFrame:
    grouped = all_results_df.groupby(["strategy_name", COL_STOCK_CODE], sort=True)
    product_metrics = grouped.agg(**_product_metric_aggregations()).reset_index()

    price_std = grouped["chosen_price"].std(ddof=0).reset_index(name="price_std")
    product_metrics = product_metrics.merge(price_std, on=["strategy_name", COL_STOCK_CODE], how="inner")
    product_metrics = product_metrics.rename(columns={"strategy_name": "strategy"})
    return _finalise_metrics_frame(product_metrics, metric_level=EVALUATION_PRODUCT_METRIC_LEVEL)


def _compute_strategy_metrics(product_metrics_df: pd.DataFrame) -> pd.DataFrame:
    strategy_metrics = product_metrics_df.groupby("strategy", sort=True).agg(**_strategy_metric_aggregations()).reset_index()
    strategy_metrics[COL_STOCK_CODE] = EVALUATION_SUMMARY_STOCK_CODE
    return _finalise_metrics_frame(strategy_metrics, metric_level=EVALUATION_STRATEGY_METRIC_LEVEL)


def _build_summary(strategy_metrics_df: pd.DataFrame) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    summary_columns = _summary_metric_columns()
    for row in strategy_metrics_df.to_dict(orient="records"):
        strategy_name = str(row["strategy"])
        summary[strategy_name] = {column: float(row[column]) for column in summary_columns}
    return summary


def compute_metrics() -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    logger.info("Evaluation metrics computation started.")
    results_by_strategy = load_strategy_results()
    all_results_df = pd.concat(results_by_strategy.values(), ignore_index=True)

    product_metrics_df = _compute_product_metrics(all_results_df)
    strategy_metrics_df = _compute_strategy_metrics(product_metrics_df)
    combined_metrics_df = pd.concat([product_metrics_df, strategy_metrics_df], ignore_index=True)
    combined_metrics_df = combined_metrics_df.sort_values(["metric_level", "strategy", COL_STOCK_CODE], kind="mergesort")
    combined_metrics_df = combined_metrics_df.reset_index(drop=True)

    summary = _build_summary(strategy_metrics_df)

    metrics_output_path = configured_path(PROJECT_ROOT, EVALUATION_STRATEGY_METRICS_PATH)
    summary_output_path = configured_path(PROJECT_ROOT, EVALUATION_STRATEGY_SUMMARY_PATH)
    metrics_output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_output_path.parent.mkdir(parents=True, exist_ok=True)

    combined_metrics_df.to_parquet(metrics_output_path, index=False)
    summary_output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    logger.info(
        "Evaluation metrics written successfully. Rows: %s | Metrics path: %s | Summary path: %s",
        len(combined_metrics_df),
        metrics_output_path,
        summary_output_path,
    )
    return combined_metrics_df, summary
