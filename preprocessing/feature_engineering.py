import logging
from pathlib import Path
import sys

import pandas as pd

# Ensure project-root imports work when executing this file directly.
if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import (
    COL_STOCK_CODE,
    DAILY_AGG_DATA_PATH,
    FEATURE_TEST_DATA_PATH,
    FEATURE_TRAIN_DATA_PATH,
    FEATURE_MONTH_COLUMNS,
    FEATURE_WEEKDAY_COLUMNS,
    PROJECT_ROOT,
    TRAIN_SPLIT_RATIO,
)
from preprocessing.common import configured_path, ensure_required_columns
from utils.data_contracts import validate_feature_data

logger = logging.getLogger(__name__)


def _input_path() -> Path:
    return configured_path(PROJECT_ROOT, DAILY_AGG_DATA_PATH)


def _train_output_path() -> Path:
    return configured_path(PROJECT_ROOT, FEATURE_TRAIN_DATA_PATH)


def _test_output_path() -> Path:
    return configured_path(PROJECT_ROOT, FEATURE_TEST_DATA_PATH)

def _add_demand_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values([COL_STOCK_CODE, "invoice_day"], kind="mergesort").copy()
    grouped_units = df.groupby(COL_STOCK_CODE)["daily_units"]

    df["lag1_units"] = grouped_units.shift(1)
    df["lag7_units"] = grouped_units.shift(7)
    # shift(1) before rolling excludes the current day from the window, preventing target leakage.
    df["rolling7_mean_units"] = (
        grouped_units.shift(1).rolling(window=7, min_periods=7).mean().reset_index(level=0, drop=True)
    )
    return df


def _add_seasonality_features(df: pd.DataFrame) -> pd.DataFrame:
    df["weekday"] = df["invoice_day"].dt.weekday
    df["month"] = df["invoice_day"].dt.month

    weekday_dummies = pd.get_dummies(df["weekday"], prefix="weekday", dtype="int8")
    month_dummies = pd.get_dummies(df["month"], prefix="month", dtype="int8")

    # Fill missing columns so the schema is complete even when a weekday or month never appears in this split.
    for col in FEATURE_WEEKDAY_COLUMNS:
        if col not in weekday_dummies.columns:
            weekday_dummies[col] = 0
    for col in FEATURE_MONTH_COLUMNS:
        if col not in month_dummies.columns:
            month_dummies[col] = 0

    weekday_dummies = weekday_dummies[FEATURE_WEEKDAY_COLUMNS]
    month_dummies = month_dummies[FEATURE_MONTH_COLUMNS]

    df = pd.concat([df, weekday_dummies, month_dummies], axis=1)
    return df


def _split_train_test(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split each product's time series chronologically at TRAIN_SPLIT_RATIO."""
    train_parts: list[pd.DataFrame] = []
    test_parts: list[pd.DataFrame] = []

    for stock_code, product_df in df.groupby(COL_STOCK_CODE, sort=False):
        product_df = product_df.sort_values("invoice_day", kind="mergesort").reset_index(drop=True)
        split_idx = int(len(product_df) * TRAIN_SPLIT_RATIO)
        if split_idx <= 0 or split_idx >= len(product_df):
            raise ValueError(
                "Feature engineering split failed for product "
                f"{stock_code}: train/test split would be empty with TRAIN_SPLIT_RATIO={TRAIN_SPLIT_RATIO}."
            )
        train_parts.append(product_df.iloc[:split_idx].copy())
        test_parts.append(product_df.iloc[split_idx:].copy())

    train_df = pd.concat(train_parts, ignore_index=True)
    test_df = pd.concat(test_parts, ignore_index=True)
    return train_df, test_df


def run_feature_engineering() -> None:
    input_path = _input_path()
    train_output_path = _train_output_path()
    test_output_path = _test_output_path()
    logger.info("Feature engineering started.")
    logger.info("Input daily dataset: %s", input_path)
    logger.info("Output feature train dataset: %s", train_output_path)
    logger.info("Output feature test dataset: %s", test_output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Daily aggregated dataset not found: {input_path}")

    df = pd.read_parquet(input_path)
    ensure_required_columns(
        df,
        [COL_STOCK_CODE, "invoice_day", "daily_units", "avg_daily_price", "daily_revenue"],
        "Feature engineering",
    )

    df["invoice_day"] = pd.to_datetime(df["invoice_day"], errors="coerce", format="mixed")
    df = df[df["invoice_day"].notna()].copy()
    if df.empty:
        raise ValueError("Feature engineering failed: no valid rows after invoice_day parsing.")

    input_rows = len(df)
    df = _add_demand_lag_features(df)
    df = _add_seasonality_features(df)

    required_feature_columns = ["lag1_units", "lag7_units", "rolling7_mean_units"]
    df = df.dropna(subset=required_feature_columns).copy()
    if df.empty:
        raise ValueError("Feature engineering failed: no rows left after lag feature creation.")

    train_df, test_df = _split_train_test(df)
    train_df = train_df.sort_values([COL_STOCK_CODE, "invoice_day"], kind="mergesort").reset_index(drop=True)
    test_df = test_df.sort_values([COL_STOCK_CODE, "invoice_day"], kind="mergesort").reset_index(drop=True)

    validate_feature_data(train_df, "train")
    validate_feature_data(test_df, "test")

    train_output_path.parent.mkdir(parents=True, exist_ok=True)
    test_output_path.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_parquet(train_output_path, index=False)
    test_df.to_parquet(test_output_path, index=False)

    logger.info(
        (
            "Feature engineering summary | input rows: %s | modeled rows after lag-drop: %s | "
            "train rows: %s | test rows: %s | products: %s"
        ),
        input_rows,
        len(df),
        len(train_df),
        len(test_df),
        df[COL_STOCK_CODE].nunique(),
    )
    logger.info("Feature engineering completed successfully.")


if __name__ == "__main__":
    run_feature_engineering()
