import logging
from pathlib import Path
import re
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
    DOCS_PATH,
    PHASE3_REPORT_FILE,
    PROJECT_ROOT,
)

logger = logging.getLogger(__name__)

CONFIGURED_ROOT_PATH = Path(PROJECT_ROOT).resolve()
INPUT_PATH = CONFIGURED_ROOT_PATH / CLEAN_DATA_PATH
SELECTION_DOC_PATH = CONFIGURED_ROOT_PATH / DOCS_PATH / PHASE3_REPORT_FILE
OUTPUT_PATH = CONFIGURED_ROOT_PATH / DAILY_AGG_DATA_PATH


def _parse_selected_products(selection_text: str) -> list[str]:
    codes: list[str] = []
    for line in selection_text.splitlines():
        match = re.match(r"^\s*\d+\.\s+([A-Za-z0-9]+)\s+-\s+.*$", line.strip())
        if match:
            codes.append(match.group(1).upper())
    unique_codes = list(dict.fromkeys(codes))
    return unique_codes


def run_phase4() -> None:
    logger.info("Phase 4 daily aggregation started.")
    logger.info("Input cleaned dataset: %s", INPUT_PATH)
    logger.info("Input selected products document: %s", SELECTION_DOC_PATH)
    logger.info("Output aggregated dataset: %s", OUTPUT_PATH)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Clean dataset not found: {INPUT_PATH}")
    if not SELECTION_DOC_PATH.exists():
        raise FileNotFoundError(f"Product selection document not found: {SELECTION_DOC_PATH}")

    selected_text = SELECTION_DOC_PATH.read_text(encoding="utf-8")
    selected_codes = _parse_selected_products(selected_text)
    if not selected_codes:
        raise ValueError("No selected products found in product selection document.")

    df = pd.read_parquet(INPUT_PATH)
    missing_cols = [c for c in [COL_STOCK_CODE, COL_INVOICE_DATE, COL_QUANTITY, COL_PRICE] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for Phase 4 aggregation: {missing_cols}")

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
