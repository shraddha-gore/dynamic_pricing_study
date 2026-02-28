# Project root
PROJECT_ROOT = "."

# Data paths
RAW_DATA_PATH = "data/raw/"
RAW_DATA_FILE = "online_retail_II_2010_2011.csv"
PROCESSED_DATA_PATH = "data/processed/"
RESULTS_PATH = "results/"
DOCS_PATH = "docs/"
LOGS_PATH = "logs/"

# Phase outputs
PHASE1_REPORT_FILE = "raw_data_report.md"
PHASE1_LOG_FILE = "phase1.log"
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

# Experimental constants (frozen)
TRAIN_SPLIT_RATIO = 0.8

PRICE_GRID_PERCENTAGE = 0.05      # ±5% candidate grid
MAX_DAILY_CHANGE = 0.03           # ±3% clamp constraint
HYBRID_SMOOTHING_ALPHA = 0.3      # 30% weight on ML price
