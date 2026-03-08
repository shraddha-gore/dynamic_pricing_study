import pandas as pd

from config import (
    COL_COUNTRY,
    COL_PRICE,
    COL_QUANTITY,
    COL_STOCK_CODE,
    PHASE2_FROZEN_COLUMNS,
    PHASE3_FROZEN_COLUMNS,
    PHASE4_FROZEN_COLUMNS,
    PHASE5_FROZEN_COLUMNS,
    PHASE5_FROZEN_FEATURE_COLUMNS,
    PHASE7_CANDIDATE_FROZEN_COLUMNS,
    PHASE7_RESULT_FROZEN_COLUMNS,
    PRICE_OUTLIER_THRESHOLD,
    SELECTED_PRODUCT_COUNT,
    TARGET_COUNTRY,
)
from preprocessing.common import ensure_required_columns


def _validate_exact_columns(df: pd.DataFrame, expected_columns: list[str], context: str) -> None:
    actual_columns = list(df.columns)
    if actual_columns != expected_columns:
        raise ValueError(
            f"{context} validation failed: schema mismatch.\n"
            f"Expected columns: {expected_columns}\n"
            f"Actual columns:   {actual_columns}"
        )


def validate_clean_transactions(df: pd.DataFrame) -> None:
    required = PHASE2_FROZEN_COLUMNS
    ensure_required_columns(df, required, "Phase 2 cleaned dataset")
    _validate_exact_columns(df, PHASE2_FROZEN_COLUMNS, "Phase 2 cleaned dataset")

    if df.empty:
        raise ValueError("Phase 2 cleaned dataset validation failed: dataset is empty.")
    if (df[COL_COUNTRY] != TARGET_COUNTRY).any():
        raise ValueError("Phase 2 cleaned dataset validation failed: non-target country found.")
    if (df[COL_QUANTITY] < 0).any():
        raise ValueError("Phase 2 cleaned dataset validation failed: negative quantity found.")
    if (df[COL_PRICE] <= 0).any():
        raise ValueError("Phase 2 cleaned dataset validation failed: non-positive price found.")
    if (df[COL_PRICE] > PRICE_OUTLIER_THRESHOLD).any():
        raise ValueError("Phase 2 cleaned dataset validation failed: outlier above threshold found.")


def validate_selected_products(df: pd.DataFrame) -> None:
    required = PHASE3_FROZEN_COLUMNS
    ensure_required_columns(df, required, "Phase 3 selected products dataset")
    _validate_exact_columns(df, PHASE3_FROZEN_COLUMNS, "Phase 3 selected products dataset")

    if df.empty:
        raise ValueError("Phase 3 selected products validation failed: dataset is empty.")
    if len(df) != SELECTED_PRODUCT_COUNT:
        raise ValueError(
            f"Phase 3 selected products validation failed: expected {SELECTED_PRODUCT_COUNT} rows, got {len(df)}."
        )
    if df[COL_STOCK_CODE].isna().any() or (df[COL_STOCK_CODE].astype("string").str.strip() == "").any():
        raise ValueError("Phase 3 selected products validation failed: missing stock code found.")


def validate_daily_aggregation(df: pd.DataFrame) -> None:
    required = PHASE4_FROZEN_COLUMNS
    ensure_required_columns(df, required, "Phase 4 daily aggregation dataset")
    _validate_exact_columns(df, PHASE4_FROZEN_COLUMNS, "Phase 4 daily aggregation dataset")

    if df.empty:
        raise ValueError("Phase 4 daily aggregation validation failed: dataset is empty.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Phase 4 daily aggregation validation failed: null stock code found.")
    if df["invoice_day"].isna().any():
        raise ValueError("Phase 4 daily aggregation validation failed: null invoice_day found.")


def validate_phase5_features(df: pd.DataFrame, split_name: str) -> None:
    weekday_columns = [f"weekday_{i}" for i in range(7)]
    month_columns = [f"month_{i}" for i in range(1, 13)]
    required = PHASE5_FROZEN_COLUMNS

    ensure_required_columns(df, required, f"Phase 5 {split_name} feature dataset")
    _validate_exact_columns(df, PHASE5_FROZEN_COLUMNS, f"Phase 5 {split_name} feature dataset")

    if df.empty:
        raise ValueError(f"Phase 5 {split_name} feature validation failed: dataset is empty.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError(f"Phase 5 {split_name} feature validation failed: null stock code found.")
    if df["invoice_day"].isna().any():
        raise ValueError(f"Phase 5 {split_name} feature validation failed: null invoice_day found.")
    if df[["daily_units", "lag1_units", "lag7_units", "rolling7_mean_units"]].isna().any().any():
        raise ValueError(
            f"Phase 5 {split_name} feature validation failed: null demand values found."
        )
    if (df[["daily_units", "lag1_units", "lag7_units", "rolling7_mean_units"]] < 0).any().any():
        raise ValueError(
            f"Phase 5 {split_name} feature validation failed: negative demand values found."
        )

    weekday_sum = df[weekday_columns].sum(axis=1)
    month_sum = df[month_columns].sum(axis=1)
    if not (weekday_sum == 1).all():
        raise ValueError(
            f"Phase 5 {split_name} feature validation failed: weekday one-hot encoding invalid."
        )
    if not (month_sum == 1).all():
        raise ValueError(
            f"Phase 5 {split_name} feature validation failed: month one-hot encoding invalid."
        )

    missing_frozen_features = [col for col in PHASE5_FROZEN_FEATURE_COLUMNS if col not in df.columns]
    if missing_frozen_features:
        raise ValueError(
            f"Phase 5 {split_name} feature validation failed: missing frozen feature columns: {missing_frozen_features}"
        )


def validate_phase7_candidates(df: pd.DataFrame) -> None:
    ensure_required_columns(df, PHASE7_CANDIDATE_FROZEN_COLUMNS, "Phase 7 candidate simulation dataset")
    _validate_exact_columns(df, PHASE7_CANDIDATE_FROZEN_COLUMNS, "Phase 7 candidate simulation dataset")

    if df.empty:
        raise ValueError("Phase 7 candidate simulation validation failed: dataset is empty.")
    if df["invoice_day"].isna().any():
        raise ValueError("Phase 7 candidate simulation validation failed: null invoice_day found.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Phase 7 candidate simulation validation failed: null stock_code found.")
    if (df["candidate_price"] <= 0).any():
        raise ValueError("Phase 7 candidate simulation validation failed: non-positive candidate price found.")
    if (df["predicted_demand"] < 0).any():
        raise ValueError("Phase 7 candidate simulation validation failed: negative predicted demand found.")
    if (df["predicted_revenue"] < 0).any():
        raise ValueError("Phase 7 candidate simulation validation failed: negative predicted revenue found.")
    if (df["candidate_rank_by_revenue"] < 1).any():
        raise ValueError("Phase 7 candidate simulation validation failed: invalid candidate rank found.")


def validate_phase7_results(df: pd.DataFrame) -> None:
    ensure_required_columns(df, PHASE7_RESULT_FROZEN_COLUMNS, "Phase 7 simulation outcome dataset")
    _validate_exact_columns(df, PHASE7_RESULT_FROZEN_COLUMNS, "Phase 7 simulation outcome dataset")

    if df.empty:
        raise ValueError("Phase 7 simulation outcome validation failed: dataset is empty.")
    if df["invoice_day"].isna().any():
        raise ValueError("Phase 7 simulation outcome validation failed: null invoice_day found.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Phase 7 simulation outcome validation failed: null stock_code found.")
    if (df["base_price"] <= 0).any():
        raise ValueError("Phase 7 simulation outcome validation failed: non-positive base price found.")
    if (df["chosen_price"] <= 0).any():
        raise ValueError("Phase 7 simulation outcome validation failed: non-positive chosen price found.")
    if (df["predicted_demand"] < 0).any():
        raise ValueError("Phase 7 simulation outcome validation failed: negative predicted demand found.")
    if (df["predicted_revenue"] < 0).any():
        raise ValueError("Phase 7 simulation outcome validation failed: negative predicted revenue found.")
