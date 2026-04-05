import logging
from pathlib import Path
import sys

import pandas as pd

# Ensure project-root imports work when executing this file directly.
if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
from preprocessing.common import configured_path, ensure_required_columns
from utils.data_contracts import validate_daily_aggregation, validate_selected_products

logger = logging.getLogger(__name__)


def _input_path() -> Path:
    return configured_path(PROJECT_ROOT, CLEAN_DATA_PATH)


def _selected_products_input_path() -> Path:
    return configured_path(PROJECT_ROOT, SELECTED_PRODUCTS_PATH)


def _output_path() -> Path:
    return configured_path(PROJECT_ROOT, DAILY_AGG_DATA_PATH)


def run_aggregate_daily() -> None:
    input_path = _input_path()
    selected_products_input_path = _selected_products_input_path()
    output_path = _output_path()
    logger.info("Aggregation started.")
    logger.info("Input cleaned dataset: %s", input_path)
    logger.info("Input selected products dataset: %s", selected_products_input_path)
    logger.info("Output aggregated dataset: %s", output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Clean dataset not found: {input_path}")
    if not selected_products_input_path.exists():
        raise FileNotFoundError(f"Selected products dataset not found: {selected_products_input_path}")

    selected_products = pd.read_parquet(selected_products_input_path)
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

    df = pd.read_parquet(input_path)
    ensure_required_columns(
        df,
        [COL_STOCK_CODE, COL_INVOICE_DATE, COL_QUANTITY, COL_PRICE],
        "Aggregation",
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
        raise ValueError("All filtered rows have invalid invoice_date values.")

    filtered["invoice_day"] = filtered[COL_INVOICE_DATE].dt.normalize()
    filtered["revenue_line"] = filtered[COL_QUANTITY] * filtered[COL_PRICE]

    daily = (
        filtered.groupby([COL_STOCK_CODE, "invoice_day"], as_index=False)
        .agg(
            daily_units=(COL_QUANTITY, "sum"),
            avg_daily_price=(COL_PRICE, "mean"),
            daily_revenue=("revenue_line", "sum"),
        )
        .sort_values([COL_STOCK_CODE, "invoice_day"])
        .reset_index(drop=True)
    )

    if daily.empty:
        raise ValueError("Daily aggregation produced no rows.")
    validate_daily_aggregation(daily)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(output_path, index=False)

    min_date = daily["invoice_day"].min()
    max_date = daily["invoice_day"].max()
    logger.info(
        (
            "Aggregation summary | input rows: %s | filtered rows: %s | output rows: %s | "
            "products: %s | date range: %s to %s"
        ),
        input_rows,
        filtered_rows,
        len(daily),
        daily[COL_STOCK_CODE].nunique(),
        min_date.date().isoformat(),
        max_date.date().isoformat(),
    )
    logger.info("Aggregation completed. Saved aggregated data to %s", output_path)


if __name__ == "__main__":
    run_aggregate_daily()
