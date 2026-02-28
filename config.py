# Project root
PROJECT_ROOT = "."

# Data paths
RAW_DATA_PATH = "data/raw/"
RAW_DATA_FILE = "online_retail_II_2010_2011.csv"
PROCESSED_DATA_PATH = "data/processed/"
CLEAN_DATA_PATH = "data/processed/clean_transactions.parquet"
RESULTS_PATH = "results/"
DOCS_PATH = "docs/"
LOGS_PATH = "logs/"

# Phase outputs
PHASE1_REPORT_FILE = "raw_data_report.md"
PHASE1_LOG_FILE = "phase1.log"
PHASE2_LOG_FILE = "phase2.log"
EXPERIMENT_LOG_FILE = "experiment.log"

# Raw dataset schema columns
COL_INVOICE = "Invoice"
COL_STOCK_CODE = "StockCode"
COL_DESCRIPTION = "Description"
COL_QUANTITY = "Quantity"
COL_INVOICE_DATE = "InvoiceDate"
COL_PRICE = "Price"
COL_CUSTOMER_ID = "Customer ID"
COL_COUNTRY = "Country"

# Experimental constants
TRAIN_SPLIT_RATIO = 0.8

PRICE_GRID_PERCENTAGE = 0.05      # ±5% candidate grid
MAX_DAILY_CHANGE = 0.03           # ±3% clamp constraint
HYBRID_SMOOTHING_ALPHA = 0.3      # 30% weight on ML price

# Phase 2 cleaning constants
TARGET_COUNTRY = "United Kingdom"
PRICE_OUTLIER_THRESHOLD = 1000.0
PRICE_OUTLIER_REVIEW_TOP_N = 20
INVOICE_CANCELLATION_PREFIX = "C"

# Validation
PHASE2_REQUIRED_COLUMNS = [
    COL_INVOICE,
    COL_STOCK_CODE,
    COL_DESCRIPTION,
    COL_QUANTITY,
    COL_INVOICE_DATE,
    COL_PRICE,
    COL_CUSTOMER_ID,
    COL_COUNTRY,
]
PHASE2_STRING_COLUMNS = [COL_INVOICE, COL_STOCK_CODE, COL_DESCRIPTION, COL_COUNTRY]
PHASE2_PRICE_DESCRIBE_PERCENTILES = [0.5, 0.9, 0.95, 0.99, 0.995, 0.999]
RAW_INSPECTION_PERCENTILES = [0.01, 0.05, 0.5, 0.95, 0.99]
