import pandas as pd

from config import (
    COL_COUNTRY,
    COL_CUSTOMER_ID,
    COL_DESCRIPTION,
    COL_INVOICE,
    COL_INVOICE_DATE,
    COL_PRICE,
    COL_QUANTITY,
    COL_STOCK_CODE,
    PRICE_OUTLIER_THRESHOLD,
    SELECTED_PRODUCT_COUNT,
    TARGET_COUNTRY,
)
from preprocessing.common import ensure_required_columns


def validate_clean_transactions(df: pd.DataFrame) -> None:
    required = [
        COL_INVOICE,
        COL_STOCK_CODE,
        COL_DESCRIPTION,
        COL_QUANTITY,
        COL_INVOICE_DATE,
        COL_PRICE,
        COL_CUSTOMER_ID,
        COL_COUNTRY,
    ]
    ensure_required_columns(df, required, "Phase 2 cleaned dataset")

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
    required = [COL_STOCK_CODE, COL_DESCRIPTION, "Revenue", "PriceStd", "ActiveDays"]
    ensure_required_columns(df, required, "Phase 3 selected products dataset")

    if df.empty:
        raise ValueError("Phase 3 selected products validation failed: dataset is empty.")
    if len(df) != SELECTED_PRODUCT_COUNT:
        raise ValueError(
            f"Phase 3 selected products validation failed: expected {SELECTED_PRODUCT_COUNT} rows, got {len(df)}."
        )
    if df[COL_STOCK_CODE].isna().any() or (df[COL_STOCK_CODE].astype("string").str.strip() == "").any():
        raise ValueError("Phase 3 selected products validation failed: missing stock code found.")


def validate_daily_aggregation(df: pd.DataFrame) -> None:
    required = [COL_STOCK_CODE, "InvoiceDay", "DailyUnits", "AvgDailyPrice", "DailyRevenue"]
    ensure_required_columns(df, required, "Phase 4 daily aggregation dataset")

    if df.empty:
        raise ValueError("Phase 4 daily aggregation validation failed: dataset is empty.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Phase 4 daily aggregation validation failed: null stock code found.")
    if df["InvoiceDay"].isna().any():
        raise ValueError("Phase 4 daily aggregation validation failed: null InvoiceDay found.")


def validate_phase5_features(df: pd.DataFrame, split_name: str) -> None:
    weekday_columns = [f"Weekday_{i}" for i in range(7)]
    month_columns = [f"Month_{i}" for i in range(1, 13)]
    required = [
        COL_STOCK_CODE,
        "InvoiceDay",
        "DailyUnits",
        "AvgDailyPrice",
        "DailyRevenue",
        "Lag1Units",
        "Lag7Units",
        "Rolling7MeanUnits",
    ] + weekday_columns + month_columns

    ensure_required_columns(df, required, f"Phase 5 {split_name} feature dataset")

    if df.empty:
        raise ValueError(f"Phase 5 {split_name} feature validation failed: dataset is empty.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError(f"Phase 5 {split_name} feature validation failed: null stock code found.")
    if df["InvoiceDay"].isna().any():
        raise ValueError(f"Phase 5 {split_name} feature validation failed: null InvoiceDay found.")
    if df[["DailyUnits", "Lag1Units", "Lag7Units", "Rolling7MeanUnits"]].isna().any().any():
        raise ValueError(
            f"Phase 5 {split_name} feature validation failed: null demand values found."
        )
    if (df[["DailyUnits", "Lag1Units", "Lag7Units", "Rolling7MeanUnits"]] < 0).any().any():
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
