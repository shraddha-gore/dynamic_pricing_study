# -----------------------------
# Project
# -----------------------------
PROJECT_ROOT = "."


# -----------------------------
# Global paths
# -----------------------------
RAW_DATA_PATH = "data/raw/"
RAW_DATA_FILE = "online_retail_II_2010_2011.csv"
PROCESSED_DATA_PATH = "data/processed/"
RESULTS_PATH = "results/"
DOCS_PATH = "docs/"
LOGS_PATH = "logs/"


# -----------------------------
# Phase output paths
# -----------------------------
# Phase 2
CLEAN_DATA_PATH = "data/processed/clean_transactions.parquet"

# Phase 3
SELECTED_PRODUCTS_PATH = "data/processed/selected_products.parquet"

# Phase 4
DAILY_AGG_DATA_PATH = "data/processed/daily_product_data.parquet"

# Phase 5
FEATURE_TRAIN_DATA_PATH = "data/processed/feature_train_data.parquet"
FEATURE_TEST_DATA_PATH = "data/processed/feature_test_data.parquet"

# Phase 6
PHASE6_MODEL_ARTIFACT_PATH = "models/artifacts/demand_model.joblib"
PHASE6_METRICS_PATH = "results/demand_model_metrics.json"


# -----------------------------
# Phase output files (docs/logs)
# -----------------------------
PHASE1_REPORT_FILE = "raw_data_report.md"
PHASE1_LOG_FILE = "phase1.log"
PHASE2_LOG_FILE = "phase2.log"
PHASE3_REPORT_FILE = "product_selection.md"
PHASE3_LOG_FILE = "phase3.log"
PHASE4_LOG_FILE = "phase4.log"
PHASE5_LOG_FILE = "phase5.log"
PHASE6_LOG_FILE = "phase6.log"
EXPERIMENT_LOG_FILE = "experiment.log"


# -----------------------------
# Raw source schema (CSV headers)
# -----------------------------
RAW_COL_INVOICE = "Invoice"
RAW_COL_STOCK_CODE = "StockCode"
RAW_COL_DESCRIPTION = "Description"
RAW_COL_QUANTITY = "Quantity"
RAW_COL_INVOICE_DATE = "InvoiceDate"
RAW_COL_PRICE = "Price"
RAW_COL_CUSTOMER_ID = "Customer ID"
RAW_COL_COUNTRY = "Country"


# -----------------------------
# Canonical schema (processed data, snake_case)
# -----------------------------
COL_INVOICE = "invoice"
COL_STOCK_CODE = "stock_code"
COL_DESCRIPTION = "description"
COL_QUANTITY = "quantity"
COL_INVOICE_DATE = "invoice_date"
COL_PRICE = "price"
COL_CUSTOMER_ID = "customer_id"
COL_COUNTRY = "country"

RAW_TO_CANONICAL_COLUMNS = {
    RAW_COL_INVOICE: COL_INVOICE,
    RAW_COL_STOCK_CODE: COL_STOCK_CODE,
    RAW_COL_DESCRIPTION: COL_DESCRIPTION,
    RAW_COL_QUANTITY: COL_QUANTITY,
    RAW_COL_INVOICE_DATE: COL_INVOICE_DATE,
    RAW_COL_PRICE: COL_PRICE,
    RAW_COL_CUSTOMER_ID: COL_CUSTOMER_ID,
    RAW_COL_COUNTRY: COL_COUNTRY,
}


# -----------------------------
# Cross-phase experimental constants
# -----------------------------
TRAIN_SPLIT_RATIO = 0.8
PRICE_GRID_PERCENTAGE = 0.05      # +/-5% candidate grid
MAX_DAILY_CHANGE = 0.03           # +/-3% clamp constraint
HYBRID_SMOOTHING_ALPHA = 0.3      # 30% weight on ML price


# -----------------------------
# Phase 1 constants
# -----------------------------
RAW_INSPECTION_PERCENTILES = [0.01, 0.05, 0.5, 0.95, 0.99]


# -----------------------------
# Phase 2 constants
# -----------------------------
TARGET_COUNTRY = "United Kingdom"
PRICE_OUTLIER_THRESHOLD = 1000.0
PRICE_OUTLIER_REVIEW_TOP_N = 20
INVOICE_CANCELLATION_PREFIX = "C"
EXCLUDED_STOCK_CODES = ["DOS", "DOT", "POST", "M", "AMAZONFEE", "B"]
PHASE2_STRING_COLUMNS = [COL_INVOICE, COL_STOCK_CODE, COL_DESCRIPTION, COL_COUNTRY]
PHASE2_PRICE_DESCRIBE_PERCENTILES = [0.5, 0.9, 0.95, 0.99, 0.995, 0.999]
PHASE2_RAW_REQUIRED_COLUMNS = [
    RAW_COL_INVOICE,
    RAW_COL_STOCK_CODE,
    RAW_COL_DESCRIPTION,
    RAW_COL_QUANTITY,
    RAW_COL_INVOICE_DATE,
    RAW_COL_PRICE,
    RAW_COL_CUSTOMER_ID,
    RAW_COL_COUNTRY,
]
PHASE2_FROZEN_COLUMNS = [
    COL_INVOICE,
    COL_STOCK_CODE,
    COL_DESCRIPTION,
    COL_QUANTITY,
    COL_INVOICE_DATE,
    COL_PRICE,
    COL_CUSTOMER_ID,
    COL_COUNTRY,
]


# -----------------------------
# Phase 3 constants
# -----------------------------
MIN_ACTIVE_DAYS = 150
SELECTED_PRODUCT_COUNT = 5
MIN_PRICE_STD = 0.0
PHASE3_FROZEN_COLUMNS = [COL_STOCK_CODE, COL_DESCRIPTION, "revenue", "price_std", "active_days"]


# -----------------------------
# Phase 4 constants
# -----------------------------
PHASE4_FROZEN_COLUMNS = [COL_STOCK_CODE, "invoice_day", "daily_units", "avg_daily_price", "daily_revenue"]


# -----------------------------
# Phase 5 constants
# -----------------------------
PHASE5_FROZEN_COLUMNS = [
    COL_STOCK_CODE,
    "invoice_day",
    "daily_units",
    "avg_daily_price",
    "daily_revenue",
    "lag1_units",
    "lag7_units",
    "rolling7_mean_units",
    "weekday",
    "month",
    "weekday_0",
    "weekday_1",
    "weekday_2",
    "weekday_3",
    "weekday_4",
    "weekday_5",
    "weekday_6",
    "month_1",
    "month_2",
    "month_3",
    "month_4",
    "month_5",
    "month_6",
    "month_7",
    "month_8",
    "month_9",
    "month_10",
    "month_11",
    "month_12",
]
PHASE5_FROZEN_FEATURE_COLUMNS = [
    "lag1_units",
    "lag7_units",
    "rolling7_mean_units",
    "avg_daily_price",
    "weekday_0",
    "weekday_1",
    "weekday_2",
    "weekday_3",
    "weekday_4",
    "weekday_5",
    "weekday_6",
    "month_1",
    "month_2",
    "month_3",
    "month_4",
    "month_5",
    "month_6",
    "month_7",
    "month_8",
    "month_9",
    "month_10",
    "month_11",
    "month_12",
]


# -----------------------------
# Phase 6 constants
# -----------------------------
PHASE6_FEATURE_COLUMNS = PHASE5_FROZEN_FEATURE_COLUMNS
PHASE6_TARGET_COLUMN = "daily_units"
