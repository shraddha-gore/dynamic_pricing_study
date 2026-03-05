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
    COL_INVOICE_DATE,
    COL_PRICE,
    COL_QUANTITY,
    COL_STOCK_CODE,
    DAILY_AGG_DATA_PATH,
    PROJECT_ROOT,
    SELECTED_PRODUCTS_PATH,
)
from preprocessing.common import configured_root, ensure_required_columns
from utils.data_contracts import validate_daily_aggregation, validate_selected_products

logger = logging.getLogger(__name__)

CONFIGURED_ROOT_PATH = configured_root(PROJECT_ROOT)
INPUT_PATH = CONFIGURED_ROOT_PATH / CLEAN_DATA_PATH
SELECTED_PRODUCTS_INPUT_PATH = CONFIGURED_ROOT_PATH / SELECTED_PRODUCTS_PATH
OUTPUT_PATH = CONFIGURED_ROOT_PATH / DAILY_AGG_DATA_PATH


def run_phase4() -> None:
    logger.info("Phase 4 daily aggregation started.")
    logger.info("Input cleaned dataset: %s", INPUT_PATH)
    logger.info("Input selected products dataset: %s", SELECTED_PRODUCTS_INPUT_PATH)
    logger.info("Output aggregated dataset: %s", OUTPUT_PATH)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Clean dataset not found: {INPUT_PATH}")
    if not SELECTED_PRODUCTS_INPUT_PATH.exists():
        raise FileNotFoundError(f"Selected products dataset not found: {SELECTED_PRODUCTS_INPUT_PATH}")

    selected_products = pd.read_parquet(SELECTED_PRODUCTS_INPUT_PATH)
    validate_selected_products(selected_products)
    selected_codes = (
        selected_products[COL_STOCK_CODE]
        .astype("string")
        .str.upper()
        .str.strip()
        .dropna()
        .tolist()
    )
    selected_codes = list(dict.fromkeys(selected_codes))

    df = pd.read_parquet(INPUT_PATH)
    ensure_required_columns(
        df,
        [COL_STOCK_CODE, COL_INVOICE_DATE, COL_QUANTITY, COL_PRICE],
        "Phase 4 aggregation",
    )

    input_rows = len(df)
    df[COL_STOCK_CODE] = df[COL_STOCK_CODE].astype("string").str.upper().str.strip()
    filtered = df[df[COL_STOCK_CODE].isin(selected_codes)].copy()
    filtered_rows = len(filtered)
    if filtered.empty:
        raise ValueError("No rows found for selected products in cleaned dataset.")

    filtered[COL_INVOICE_DATE] = pd.to_datetime(filtered[COL_INVOICE_DATE], errors="coerce", format="mixed")
    filtered = filtered[filtered[COL_INVOICE_DATE].notna()].copy()
    if filtered.empty:
        raise ValueError("All filtered rows have invalid InvoiceDate values.")

    filtered["InvoiceDay"] = filtered[COL_INVOICE_DATE].dt.normalize()
    filtered["RevenueLine"] = filtered[COL_QUANTITY] * filtered[COL_PRICE]

    daily = (
        filtered.groupby([COL_STOCK_CODE, "InvoiceDay"], as_index=False)
        .agg(
            DailyUnits=(COL_QUANTITY, "sum"),
            AvgDailyPrice=(COL_PRICE, "mean"),
            DailyRevenue=("RevenueLine", "sum"),
        )
        .sort_values([COL_STOCK_CODE, "InvoiceDay"])
        .reset_index(drop=True)
    )

    if daily.empty:
        raise ValueError("Daily aggregation produced no rows.")
    validate_daily_aggregation(daily)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(OUTPUT_PATH, index=False)

    min_date = daily["InvoiceDay"].min()
    max_date = daily["InvoiceDay"].max()
    logger.info(
        (
            "Phase 4 summary | input rows: %s | filtered rows: %s | output rows: %s | "
            "products: %s | date range: %s to %s"
        ),
        input_rows,
        filtered_rows,
        len(daily),
        daily[COL_STOCK_CODE].nunique(),
        min_date.date().isoformat(),
        max_date.date().isoformat(),
    )
    logger.info("Phase 4 daily aggregation completed. Saved aggregated data to %s", OUTPUT_PATH)


if __name__ == "__main__":
    run_phase4()
