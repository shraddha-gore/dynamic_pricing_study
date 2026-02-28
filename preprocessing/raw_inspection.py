import logging
from pathlib import Path
import sys

import pandas as pd

# Ensure project-root imports work when executing this file directly.
PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from config import (
    COL_COUNTRY,
    COL_INVOICE,
    COL_INVOICE_DATE,
    COL_PRICE,
    COL_QUANTITY,
    DOCS_PATH,
    PHASE1_REPORT_FILE,
    PROJECT_ROOT,
    RAW_DATA_FILE,
    RAW_DATA_PATH,
)

CONFIGURED_ROOT_PATH = Path(PROJECT_ROOT).resolve()
CSV_PATH = CONFIGURED_ROOT_PATH / RAW_DATA_PATH / RAW_DATA_FILE
REPORT_PATH = CONFIGURED_ROOT_PATH / DOCS_PATH / PHASE1_REPORT_FILE
logger = logging.getLogger(__name__)


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df.head(max_rows) if max_rows else df
    if view.empty:
        return "_No rows_"

    headers = [str(col) for col in view.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in view.iterrows():
        cells = [str(row[col]) for col in view.columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_report(df: pd.DataFrame) -> str:
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
    if COL_INVOICE in df.columns:
        cancellation_mask = df[COL_INVOICE].astype(str).str.startswith("C", na=False)
        cancellations = int(cancellation_mask.sum())
        cancellation_pct = (cancellations / len(df)) * 100 if len(df) else 0.0

    quantity_stats = (
        df[COL_QUANTITY].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99]).to_frame().reset_index()
        if COL_QUANTITY in df.columns
        else pd.DataFrame(columns=["index", COL_QUANTITY])
    )
    price_stats = (
        df[COL_PRICE].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99]).to_frame().reset_index()
        if COL_PRICE in df.columns
        else pd.DataFrame(columns=["index", COL_PRICE])
    )

    quantity_quality = pd.DataFrame(
        [
            {"metric": "negative_quantity_rows", "value": int((df[COL_QUANTITY] < 0).sum()) if COL_QUANTITY in df.columns else 0},
            {"metric": "zero_quantity_rows", "value": int((df[COL_QUANTITY] == 0).sum()) if COL_QUANTITY in df.columns else 0},
        ]
    )

    price_quality = pd.DataFrame(
        [
            {"metric": "negative_price_rows", "value": int((df[COL_PRICE] < 0).sum()) if COL_PRICE in df.columns else 0},
            {"metric": "zero_price_rows", "value": int((df[COL_PRICE] == 0).sum()) if COL_PRICE in df.columns else 0},
        ]
    )

    country_distribution = (
        df[COL_COUNTRY].value_counts(dropna=False).rename_axis("country").reset_index(name="row_count")
        if COL_COUNTRY in df.columns
        else pd.DataFrame(columns=["country", "row_count"])
    )

    if COL_QUANTITY in df.columns and COL_PRICE in df.columns and COL_COUNTRY in df.columns:
        revenue_frame = df.copy()
        revenue_frame["Revenue"] = revenue_frame[COL_QUANTITY] * revenue_frame[COL_PRICE]
        revenue_country = (
            revenue_frame.groupby(COL_COUNTRY, dropna=False)["Revenue"]
            .sum()
            .sort_values(ascending=False)
            .rename_axis("country")
            .reset_index()
        )
    else:
        revenue_country = pd.DataFrame(columns=["country", "Revenue"])

    date_range_text = f"{COL_INVOICE_DATE} column not found."
    if COL_INVOICE_DATE in df.columns:
        parsed_dates = pd.to_datetime(df[COL_INVOICE_DATE], errors="coerce", format="mixed")
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

    report_lines = [
        "# Raw Data Inspection Report",
        "",
        "## Source",
        f"- File: `{CSV_PATH}`",
        "- Phase: 1 (Raw Data Inspection)",
        "",
        "## Dataset Shape",
        f"- Rows: {shape_rows:,}",
        f"- Columns: {shape_cols:,}",
        "",
        "## Columns and Data Types",
        dataframe_to_markdown(column_types),
        "",
        "## Null Count and Percentage",
        dataframe_to_markdown(null_summary),
        "",
        "## Cancellation Invoices",
        f"- Rows with `Invoice` starting with `C`: {cancellations:,} ({cancellation_pct:.2f}%)",
        "",
        "## Quantity Distribution",
        dataframe_to_markdown(quantity_stats),
        "",
        "### Quantity Quality Flags",
        dataframe_to_markdown(quantity_quality),
        "",
        "## Price Distribution",
        dataframe_to_markdown(price_stats),
        "",
        "### Price Quality Flags",
        dataframe_to_markdown(price_quality),
        "",
        "## Country Distribution (Rows)",
        dataframe_to_markdown(country_distribution, max_rows=20),
        "",
        "## Revenue per Country (Raw)",
        dataframe_to_markdown(revenue_country, max_rows=20),
        "",
        "## Date Range Validation",
        f"- {date_range_text}",
        "",
        "## Frozen Decisions for Next Phase",
        "- Keep UK only",
        "- Remove cancelled invoices",
        "- Remove negative quantities",
        "- Remove zero or negative prices",
        "- Temporal boundary already fixed at source (2010–2011 only)",
    ]
    return "\n".join(report_lines)


def run_phase1() -> None:
    logger.info("Phase 1 raw inspection started.")

    if not CSV_PATH.exists():
        logger.error("Dataset missing at %s", CSV_PATH)
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(df)
    REPORT_PATH.write_text(report, encoding="utf-8")
    logger.info("Phase 1 raw inspection completed. Report saved to %s", REPORT_PATH)


if __name__ == "__main__":
    run_phase1()
