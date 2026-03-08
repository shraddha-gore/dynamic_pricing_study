import json
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
    COL_DESCRIPTION,
    COL_INVOICE_DATE,
    COL_PRICE,
    COL_QUANTITY,
    COL_STOCK_CODE,
    MIN_ACTIVE_DAYS,
    MIN_PRICE_STD,
    PHASE3_REPORT_FILE,
    PROJECT_ROOT,
    REPORTS_PATH,
    SELECTED_PRODUCTS_PATH,
    SELECTED_PRODUCT_COUNT,
)
from preprocessing.common import configured_root, ensure_required_columns
from utils.data_contracts import validate_selected_products

logger = logging.getLogger(__name__)

CONFIGURED_ROOT_PATH = configured_root(PROJECT_ROOT)
INPUT_PATH = CONFIGURED_ROOT_PATH / CLEAN_DATA_PATH
REPORT_PATH = CONFIGURED_ROOT_PATH / REPORTS_PATH / PHASE3_REPORT_FILE
SELECTED_PRODUCTS_OUTPUT_PATH = CONFIGURED_ROOT_PATH / SELECTED_PRODUCTS_PATH


def _validate_columns(df: pd.DataFrame) -> None:
    ensure_required_columns(
        df,
        [
            COL_STOCK_CODE,
            COL_DESCRIPTION,
            COL_INVOICE_DATE,
            COL_PRICE,
            COL_QUANTITY,
        ],
        "Phase 3 product selection",
    )


def _build_description_map(df: pd.DataFrame) -> pd.Series:
    non_empty = (
        df[[COL_STOCK_CODE, COL_DESCRIPTION]]
        .dropna(subset=[COL_STOCK_CODE, COL_DESCRIPTION])
        .copy()
    )
    non_empty[COL_DESCRIPTION] = non_empty[COL_DESCRIPTION].astype("string").str.strip()
    non_empty = non_empty[non_empty[COL_DESCRIPTION] != ""]
    if non_empty.empty:
        return pd.Series(dtype="string")

    # Use the most frequent description for each stock code to handle minor text variants.
    return non_empty.groupby(COL_STOCK_CODE)[COL_DESCRIPTION].agg(lambda s: s.mode().iloc[0])


def _build_report_payload(metrics: pd.DataFrame, eligible: pd.DataFrame, selected: pd.DataFrame) -> dict[str, object]:
    return {
        "phase": 3,
        "name": "product_selection",
        "selection_parameters": {
            "min_price_std": float(MIN_PRICE_STD),
            "min_active_days": int(MIN_ACTIVE_DAYS),
            "selected_product_count": int(SELECTED_PRODUCT_COUNT),
        },
        "run_summary": {
            "products_analyzed": int(len(metrics)),
            "eligible_products": int(len(eligible)),
            "selected_products": int(len(selected)),
        },
        "selected_products": selected.to_dict(orient="records"),
    }


def run_phase3() -> None:
    logger.info("Phase 3 product selection started.")
    logger.info("Input dataset: %s", INPUT_PATH)
    logger.info("Output report: %s", REPORT_PATH)
    logger.info("Output selected products dataset: %s", SELECTED_PRODUCTS_OUTPUT_PATH)

    if not INPUT_PATH.exists():
        logger.error("Clean dataset missing at %s", INPUT_PATH)
        raise FileNotFoundError(f"Dataset not found: {INPUT_PATH}")

    df = pd.read_parquet(INPUT_PATH)
    _validate_columns(df)
    df[COL_INVOICE_DATE] = pd.to_datetime(df[COL_INVOICE_DATE], errors="coerce", format="mixed")
    invalid_dates = int(df[COL_INVOICE_DATE].isna().sum())
    if invalid_dates:
        logger.info("Dropping rows with invalid invoice dates in Phase 3: %s", invalid_dates)
        df = df[df[COL_INVOICE_DATE].notna()].copy()

    if df.empty:
        raise ValueError("Phase 3 cannot continue: cleaned dataset is empty after date validation.")

    df["invoice_day"] = df[COL_INVOICE_DATE].dt.date
    df["revenue_line"] = df[COL_PRICE] * df[COL_QUANTITY]

    metrics = (
        df.groupby(COL_STOCK_CODE)
        .agg(
            revenue=("revenue_line", "sum"),
            price_std=(COL_PRICE, "std"),
            active_days=("invoice_day", "nunique"),
        )
        .reset_index()
    )
    logger.info("Computed product-level metrics for %s products.", len(metrics))

    eligible = metrics[
        (metrics["price_std"] > MIN_PRICE_STD) & (metrics["active_days"] >= MIN_ACTIVE_DAYS)
    ].copy()
    logger.info(
        "Products passing filters (price_std > %.4f and active_days >= %s): %s",
        MIN_PRICE_STD,
        MIN_ACTIVE_DAYS,
        len(eligible),
    )

    selected = (
        eligible.sort_values("revenue", ascending=False)
        .head(SELECTED_PRODUCT_COUNT)
        .copy()
    )

    description_map = _build_description_map(df)
    selected[COL_DESCRIPTION] = selected[COL_STOCK_CODE].map(description_map).fillna("UNKNOWN DESCRIPTION")
    selected = selected[
        [COL_STOCK_CODE, COL_DESCRIPTION, "revenue", "price_std", "active_days"]
    ].reset_index(drop=True)

    validate_selected_products(selected)
    logger.info("Selected top %s products for downstream phases.", SELECTED_PRODUCT_COUNT)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SELECTED_PRODUCTS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    selected.to_parquet(SELECTED_PRODUCTS_OUTPUT_PATH, index=False)
    report_payload = _build_report_payload(metrics, eligible, selected)
    REPORT_PATH.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    logger.info(
        "Phase 3 product selection completed. Saved report to %s and selected products to %s",
        REPORT_PATH,
        SELECTED_PRODUCTS_OUTPUT_PATH,
    )


if __name__ == "__main__":
    run_phase3()
