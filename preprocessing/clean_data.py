import logging
from pathlib import Path
import sys

import pandas as pd

# Ensure project-root imports work when executing this file directly.
PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from config import (
    CLEAN_DATA_PATH,
    COL_CUSTOMER_ID,
    COL_DESCRIPTION,
    COL_COUNTRY,
    COL_INVOICE,
    COL_INVOICE_DATE,
    COL_PRICE,
    COL_QUANTITY,
    COL_STOCK_CODE,
    INVOICE_CANCELLATION_PREFIX,
    PHASE2_PRICE_DESCRIBE_PERCENTILES,
    PHASE2_REQUIRED_COLUMNS,
    PHASE2_STRING_COLUMNS,
    PRICE_OUTLIER_REVIEW_TOP_N,
    PRICE_OUTLIER_THRESHOLD,
    PROJECT_ROOT,
    RAW_DATA_FILE,
    RAW_DATA_PATH,
    TARGET_COUNTRY,
)

CONFIGURED_ROOT_PATH = Path(PROJECT_ROOT).resolve()
CSV_PATH = CONFIGURED_ROOT_PATH / RAW_DATA_PATH / RAW_DATA_FILE
OUTPUT_PATH = CONFIGURED_ROOT_PATH / CLEAN_DATA_PATH

logger = logging.getLogger(__name__)


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in PHASE2_REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for Phase 2 cleaning: {missing}")


def _standardize_strings(df: pd.DataFrame) -> pd.DataFrame:
    for col in PHASE2_STRING_COLUMNS:
        df[col] = df[col].astype("string").str.strip()
    df[COL_INVOICE] = df[COL_INVOICE].str.upper()
    df[COL_STOCK_CODE] = df[COL_STOCK_CODE].str.upper()
    df[COL_DESCRIPTION] = df[COL_DESCRIPTION].str.replace(r"\s+", " ", regex=True).str.strip()
    return df


def _coerce_and_validate_types(df: pd.DataFrame) -> pd.DataFrame:
    quantity_numeric = pd.to_numeric(df[COL_QUANTITY], errors="coerce")
    invalid_quantity_rows = int(quantity_numeric.isna().sum())
    if invalid_quantity_rows:
        logger.info("Dropping rows with non-numeric quantities: %s", invalid_quantity_rows)
    df = df[quantity_numeric.notna()].copy()
    df[COL_QUANTITY] = quantity_numeric[quantity_numeric.notna()]

    price_numeric = pd.to_numeric(df[COL_PRICE], errors="coerce")
    invalid_price_rows = int(price_numeric.isna().sum())
    if invalid_price_rows:
        logger.info("Dropping rows with non-numeric prices: %s", invalid_price_rows)
    df = df[price_numeric.notna()].copy()
    df[COL_PRICE] = price_numeric[price_numeric.notna()]

    invoice_datetime = pd.to_datetime(df[COL_INVOICE_DATE], errors="coerce", format="mixed")
    invalid_date_rows = int(invoice_datetime.isna().sum())
    if invalid_date_rows:
        logger.info("Dropping rows with unparseable invoice dates: %s", invalid_date_rows)
    df = df[invoice_datetime.notna()].copy()
    df[COL_INVOICE_DATE] = invoice_datetime[invoice_datetime.notna()]

    customer_numeric = pd.to_numeric(df[COL_CUSTOMER_ID], errors="coerce")
    df[COL_CUSTOMER_ID] = customer_numeric.astype("Int64")

    return df


def _log_price_distribution(df: pd.DataFrame) -> None:
    positive_prices = df[df[COL_PRICE] > 0][COL_PRICE]
    if positive_prices.empty:
        logger.warning("No positive prices available for outlier inspection.")
        return

    summary = positive_prices.describe(percentiles=PHASE2_PRICE_DESCRIBE_PERCENTILES)
    logger.info("Positive price distribution summary:\n%s", summary.to_string())

    top_prices = (
        positive_prices.sort_values(ascending=False)
        .drop_duplicates()
        .head(PRICE_OUTLIER_REVIEW_TOP_N)
    )
    logger.info(
        "Top %s unique positive prices (descending):\n%s",
        PRICE_OUTLIER_REVIEW_TOP_N,
        top_prices.to_string(index=False),
    )

    highest_rows = (
        df[df[COL_PRICE] > 0]
        .sort_values(COL_PRICE, ascending=False)
        [[COL_INVOICE, COL_STOCK_CODE, COL_DESCRIPTION, COL_QUANTITY, COL_PRICE, COL_INVOICE_DATE]]
        .head(PRICE_OUTLIER_REVIEW_TOP_N)
    )
    logger.info(
        "Top %s rows by positive price:\n%s",
        PRICE_OUTLIER_REVIEW_TOP_N,
        highest_rows.to_string(index=False),
    )


def _run_quality_checks(df: pd.DataFrame) -> None:
    if not (df[COL_COUNTRY] == TARGET_COUNTRY).all():
        raise ValueError("Country normalization check failed: non-target country values remain.")
    if (df[COL_QUANTITY] < 0).any():
        raise ValueError("Quantity quality check failed: negative quantities remain.")
    if (df[COL_PRICE] <= 0).any():
        raise ValueError("Price quality check failed: non-positive prices remain.")
    if (df[COL_PRICE] > PRICE_OUTLIER_THRESHOLD).any():
        raise ValueError("Price quality check failed: outlier prices above threshold remain.")

    required_non_null_columns = [
        COL_INVOICE,
        COL_STOCK_CODE,
        COL_DESCRIPTION,
        COL_QUANTITY,
        COL_INVOICE_DATE,
        COL_PRICE,
        COL_COUNTRY,
    ]
    null_counts = df[required_non_null_columns].isna().sum()
    violating = {col: int(count) for col, count in null_counts.items() if int(count) > 0}
    if violating:
        raise ValueError(f"Non-null quality check failed: {violating}")


def run_phase2() -> None:
    logger.info("Phase 2 data cleaning started.")
    logger.info("Input dataset: %s", CSV_PATH)
    logger.info("Output dataset: %s", OUTPUT_PATH)

    if not CSV_PATH.exists():
        logger.error("Dataset missing at %s", CSV_PATH)
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    _validate_columns(df)
    df = _standardize_strings(df)
    df = _coerce_and_validate_types(df)
    logger.info("Initial row count: %s", len(df))

    country_mask = (
        df[COL_COUNTRY].astype("string").str.strip().str.lower()
        == TARGET_COUNTRY.lower()
    )
    removed_non_uk = int((~country_mask).sum())
    df = df[country_mask].copy()
    df[COL_COUNTRY] = df[COL_COUNTRY].astype("string")
    logger.info("Removed non-UK rows: %s | Remaining: %s", removed_non_uk, len(df))

    cancelled_mask = df[COL_INVOICE].astype(str).str.startswith(INVOICE_CANCELLATION_PREFIX, na=False)
    removed_cancelled = int(cancelled_mask.sum())
    df = df[~cancelled_mask].copy()
    logger.info("Removed cancelled invoice rows: %s | Remaining: %s", removed_cancelled, len(df))

    negative_qty_mask = df[COL_QUANTITY] < 0
    removed_negative_qty = int(negative_qty_mask.sum())
    df = df[~negative_qty_mask].copy()
    logger.info("Removed negative-quantity rows: %s | Remaining: %s", removed_negative_qty, len(df))
    df[COL_QUANTITY] = df[COL_QUANTITY].astype("int64")

    non_positive_price_mask = df[COL_PRICE] <= 0
    removed_non_positive_price = int(non_positive_price_mask.sum())
    df = df[~non_positive_price_mask].copy()
    logger.info("Removed non-positive-price rows: %s | Remaining: %s", removed_non_positive_price, len(df))

    _log_price_distribution(df)

    outlier_mask = df[COL_PRICE] > PRICE_OUTLIER_THRESHOLD
    removed_outliers = int(outlier_mask.sum())
    df = df[~outlier_mask].copy()
    logger.info(
        "Removed economically implausible outlier rows (price > %.2f): %s | Remaining: %s",
        PRICE_OUTLIER_THRESHOLD,
        removed_outliers,
        len(df),
    )

    _run_quality_checks(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    logger.info("Phase 2 data cleaning completed. Saved cleaned data to %s", OUTPUT_PATH)


if __name__ == "__main__":
    run_phase2()
