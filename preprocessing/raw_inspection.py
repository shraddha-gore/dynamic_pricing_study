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
    INVOICE_CANCELLATION_PREFIX,
    PHASE1_REPORT_FILE,
    PROJECT_ROOT,
    RAW_COL_COUNTRY,
    RAW_COL_INVOICE,
    RAW_COL_INVOICE_DATE,
    RAW_COL_PRICE,
    RAW_COL_QUANTITY,
    RAW_DATA_FILE,
    RAW_INSPECTION_PERCENTILES,
    RAW_DATA_PATH,
    REPORTS_PATH,
)

CONFIGURED_ROOT_PATH = Path(PROJECT_ROOT).resolve()
CSV_PATH = CONFIGURED_ROOT_PATH / RAW_DATA_PATH / RAW_DATA_FILE
REPORT_PATH = CONFIGURED_ROOT_PATH / REPORTS_PATH / PHASE1_REPORT_FILE
logger = logging.getLogger(__name__)


def _records(df: pd.DataFrame, max_rows: int | None = None) -> list[dict[str, object]]:
    view = df.head(max_rows) if max_rows else df
    return view.to_dict(orient="records")


def build_report_payload(df: pd.DataFrame) -> dict[str, object]:
    shape_rows, shape_cols = df.shape

    column_types = pd.DataFrame(
        {
            "column": df.columns,
            "dtype": [str(dtype) for dtype in df.dtypes],
        }
    )

    null_counts = df.isna().sum()
    null_percent = (null_counts / len(df)) * 100
    null_summary = pd.DataFrame(
        {
            "column": df.columns,
            "null_count": [int(null_counts[col]) for col in df.columns],
            "null_percent": [round(float(null_percent[col]), 4) for col in df.columns],
        }
    ).sort_values(["null_count", "null_percent"], ascending=False)

    cancellations = 0
    cancellation_pct = 0.0
    if RAW_COL_INVOICE in df.columns:
        cancellation_mask = df[RAW_COL_INVOICE].astype(str).str.startswith(INVOICE_CANCELLATION_PREFIX, na=False)
        cancellations = int(cancellation_mask.sum())
        cancellation_pct = (cancellations / len(df)) * 100 if len(df) else 0.0

    quantity_stats = (
        df[RAW_COL_QUANTITY].describe(percentiles=RAW_INSPECTION_PERCENTILES).to_frame().reset_index()
        if RAW_COL_QUANTITY in df.columns
        else pd.DataFrame(columns=["index", RAW_COL_QUANTITY])
    )
    price_stats = (
        df[RAW_COL_PRICE].describe(percentiles=RAW_INSPECTION_PERCENTILES).to_frame().reset_index()
        if RAW_COL_PRICE in df.columns
        else pd.DataFrame(columns=["index", RAW_COL_PRICE])
    )

    quantity_quality = pd.DataFrame(
        [
            {"metric": "negative_quantity_rows", "value": int((df[RAW_COL_QUANTITY] < 0).sum()) if RAW_COL_QUANTITY in df.columns else 0},
            {"metric": "zero_quantity_rows", "value": int((df[RAW_COL_QUANTITY] == 0).sum()) if RAW_COL_QUANTITY in df.columns else 0},
        ]
    )

    price_quality = pd.DataFrame(
        [
            {"metric": "negative_price_rows", "value": int((df[RAW_COL_PRICE] < 0).sum()) if RAW_COL_PRICE in df.columns else 0},
            {"metric": "zero_price_rows", "value": int((df[RAW_COL_PRICE] == 0).sum()) if RAW_COL_PRICE in df.columns else 0},
        ]
    )

    country_distribution = (
        df[RAW_COL_COUNTRY].value_counts(dropna=False).rename_axis("country").reset_index(name="row_count")
        if RAW_COL_COUNTRY in df.columns
        else pd.DataFrame(columns=["country", "row_count"])
    )

    if RAW_COL_QUANTITY in df.columns and RAW_COL_PRICE in df.columns and RAW_COL_COUNTRY in df.columns:
        revenue_frame = df.copy()
        revenue_frame["Revenue"] = revenue_frame[RAW_COL_QUANTITY] * revenue_frame[RAW_COL_PRICE]
        revenue_country = (
            revenue_frame.groupby(RAW_COL_COUNTRY, dropna=False)["Revenue"]
            .sum()
            .sort_values(ascending=False)
            .rename_axis("country")
            .reset_index()
        )
    else:
        revenue_country = pd.DataFrame(columns=["country", "Revenue"])

    date_range_text = f"{RAW_COL_INVOICE_DATE} column not found."
    if RAW_COL_INVOICE_DATE in df.columns:
        parsed_dates = pd.to_datetime(df[RAW_COL_INVOICE_DATE], errors="coerce", format="mixed")
        min_date = parsed_dates.min()
        max_date = parsed_dates.max()
        missing_dates = int(parsed_dates.isna().sum())
        if pd.notna(min_date) and pd.notna(max_date):
            date_range_text = (
                f"Min date: {min_date.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"Max date: {max_date.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"Unparseable rows: {missing_dates:,}"
            )
        else:
            date_range_text = f"Unable to parse valid dates. Unparseable rows: {missing_dates:,}"

    return {
        "phase": 1,
        "name": "raw_data_inspection",
        "source_file": str(CSV_PATH),
        "dataset_shape": {"rows": int(shape_rows), "columns": int(shape_cols)},
        "column_types": _records(column_types),
        "null_summary": _records(null_summary),
        "cancellation_summary": {
            "invoice_prefix": INVOICE_CANCELLATION_PREFIX,
            "cancellation_rows": int(cancellations),
            "cancellation_percent": round(float(cancellation_pct), 4),
        },
        "quantity_distribution": _records(quantity_stats),
        "quantity_quality_flags": _records(quantity_quality),
        "price_distribution": _records(price_stats),
        "price_quality_flags": _records(price_quality),
        "country_distribution_top20": _records(country_distribution, max_rows=20),
        "revenue_by_country_top20": _records(revenue_country, max_rows=20),
        "date_range_validation": date_range_text,
        "frozen_decisions_for_next_phase": [
            "Keep UK only",
            "Remove cancelled invoices",
            "Remove negative quantities",
            "Remove zero or negative prices",
            "Temporal boundary already fixed at source (2010-2011 only)",
        ],
    }


def run_phase1() -> None:
    logger.info("Phase 1 raw inspection started.")

    if not CSV_PATH.exists():
        logger.error("Dataset missing at %s", CSV_PATH)
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report_payload = build_report_payload(df)
    REPORT_PATH.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    logger.info("Phase 1 raw inspection completed. Report saved to %s", REPORT_PATH)


if __name__ == "__main__":
    run_phase1()
