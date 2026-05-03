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
LOGS_PATH = "logs/"


# -----------------------------
# Processed data artifacts
# -----------------------------
# Cleaning
CLEAN_DATA_PATH = "data/processed/clean_transactions.parquet"

# Product selection
SELECTED_PRODUCTS_PATH = "data/processed/selected_products.parquet"

# Aggregation
DAILY_AGG_DATA_PATH = "data/processed/daily_product_data.parquet"

# Feature engineering
FEATURE_TRAIN_DATA_PATH = "data/processed/feature_train_data.parquet"
FEATURE_TEST_DATA_PATH = "data/processed/feature_test_data.parquet"

# Model artifacts
MODEL_ARTIFACT_PATH = "models/artifacts/demand_model.joblib"
MODEL_METRICS_PATH = "results/metrics/demand_model_metrics.json"

# Evaluation artifacts
EVALUATION_STRATEGY_METRICS_PATH = "results/metrics/strategy_metrics.parquet"
EVALUATION_STRATEGY_SUMMARY_PATH = "results/metrics/strategy_summary.json"
EVALUATION_STATISTICAL_TESTS_PATH = "results/metrics/statistical_tests.json"


# -----------------------------
# Report and log files
# -----------------------------
RAW_INSPECTION_REPORT_FILE = "raw_inspection_report.json"
PRODUCT_SELECTION_REPORT_FILE = "product_selection_report.json"
BUILD_LOG_FILE = "build.log"
SIMULATION_LOG_FILE = "simulate.log"
EVALUATION_LOG_FILE = "evaluate.log"
DASHBOARD_LOG_FILE = "dashboard.log"
MASTER_LOG_FILE = "master.log"


# -----------------------------
# Report artifact directories
# -----------------------------
REPORTS_PATH = "results/reports/"


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
# Cross-domain experimental constants
# -----------------------------
TRAIN_SPLIT_RATIO = 0.8
PRICE_GRID_PERCENTAGE = 0.05      # +/-5% candidate grid
MAX_DAILY_CHANGE = 0.03           # +/-3% clamp constraint
HYBRID_SMOOTHING_ALPHA = 0.3      # 30% weight on ML price
RULE_PRICE_INCREASE = 0.02        # +2% adjustment for rule strategy
RULE_PRICE_DECREASE = 0.02        # -2% adjustment for rule strategy


# -----------------------------
# Inspection constants
# -----------------------------
RAW_INSPECTION_PERCENTILES = [0.01, 0.05, 0.5, 0.95, 0.99]


# -----------------------------
# Cleaning constants
# -----------------------------
TARGET_COUNTRY = "United Kingdom"
PRICE_OUTLIER_THRESHOLD = 1000.0
PRICE_OUTLIER_REVIEW_TOP_N = 20
INVOICE_CANCELLATION_PREFIX = "C"
EXCLUDED_STOCK_CODES = ["DOS", "DOT", "POST", "M", "AMAZONFEE", "B"]
CLEANING_STRING_COLUMNS = [COL_INVOICE, COL_STOCK_CODE, COL_DESCRIPTION, COL_COUNTRY]
CLEANING_PRICE_DESCRIBE_PERCENTILES = [0.5, 0.9, 0.95, 0.99, 0.995, 0.999]
CLEANING_RAW_REQUIRED_COLUMNS = [
    RAW_COL_INVOICE,
    RAW_COL_STOCK_CODE,
    RAW_COL_DESCRIPTION,
    RAW_COL_QUANTITY,
    RAW_COL_INVOICE_DATE,
    RAW_COL_PRICE,
    RAW_COL_CUSTOMER_ID,
    RAW_COL_COUNTRY,
]
CLEANING_FROZEN_COLUMNS = [
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
# Product selection constants
# -----------------------------
MIN_ACTIVE_DAYS = 150
SELECTED_PRODUCT_COUNT = 5
MIN_PRICE_STD = 0.0
PRODUCT_SELECTION_FROZEN_COLUMNS = [COL_STOCK_CODE, COL_DESCRIPTION, "revenue", "price_std", "active_days"]


# -----------------------------
# Aggregation constants
# -----------------------------
DAILY_AGGREGATION_FROZEN_COLUMNS = [COL_STOCK_CODE, "invoice_day", "daily_units", "avg_daily_price", "daily_revenue"]


# -----------------------------
# Feature engineering constants
# -----------------------------
FEATURE_DATA_FROZEN_COLUMNS = [
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
FEATURE_WEEKDAY_COLUMNS = [f"weekday_{i}" for i in range(7)]
FEATURE_MONTH_COLUMNS = [f"month_{i}" for i in range(1, 13)]
MODEL_FEATURE_COLUMNS = [
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
# Model training constants
# -----------------------------
MODEL_TYPE = "LinearRegression"
MODEL_TARGET_COLUMN = "daily_units"


# -----------------------------
# Execution naming constants
# -----------------------------
BUILD_GROUP = "build"

INSPECT_UNIT = "inspect"
CLEAN_UNIT = "clean"
SELECT_PRODUCTS_UNIT = "select_products"
AGGREGATE_DAILY_UNIT = "aggregate_daily"
FEATURE_ENGINEERING_UNIT = "feature_engineering"
TRAIN_MODEL_UNIT = "train_model"

SIMULATE_COMMAND = "simulate"
EVALUATE_COMMAND = "evaluate"
DASHBOARD_COMMAND = "dashboard"

BUILD_UNITS = (
    INSPECT_UNIT,
    CLEAN_UNIT,
    SELECT_PRODUCTS_UNIT,
    AGGREGATE_DAILY_UNIT,
    FEATURE_ENGINEERING_UNIT,
    TRAIN_MODEL_UNIT,
)

GROUP_UNITS = {
    BUILD_GROUP: BUILD_UNITS,
}

COMMAND_LOGGING_TARGETS = {
    BUILD_GROUP: (BUILD_GROUP,),
    SIMULATE_COMMAND: (SIMULATE_COMMAND,),
    EVALUATE_COMMAND: (EVALUATE_COMMAND,),
    DASHBOARD_COMMAND: (DASHBOARD_COMMAND,),
}


# -----------------------------
# Simulation constants
# -----------------------------
SIMULATION_STRATEGIES = ("rule", "ml", "hybrid")
SIMULATION_GRID_POINTS = 5
SIMULATION_OUTPUT_PATH = "results/simulation/"
SIMULATION_CANDIDATE_PATHS = {
    "rule": "results/simulation/rule_candidates.parquet",
    "ml": "results/simulation/ml_candidates.parquet",
    "hybrid": "results/simulation/hybrid_candidates.parquet",
}
SIMULATION_RESULTS_PATHS = {
    "rule": "results/simulation/rule_results.parquet",
    "ml": "results/simulation/ml_results.parquet",
    "hybrid": "results/simulation/hybrid_results.parquet",
}
SIMULATION_CANDIDATE_FROZEN_COLUMNS = [
    "invoice_day",
    COL_STOCK_CODE,
    "candidate_price",
    "predicted_demand",
    "predicted_revenue",
    "candidate_rank_by_revenue",
]
SIMULATION_RESULT_FROZEN_COLUMNS = [
    "invoice_day",
    COL_STOCK_CODE,
    "base_price",
    "previous_price",
    "chosen_price",
    "price_change",
    "abs_price_change",
    "predicted_demand",
    "predicted_revenue",
    "strategy_name",
]


# -----------------------------
# Evaluation constants
# -----------------------------
EVALUATION_METRIC_COLUMNS = [
    COL_STOCK_CODE,
    "strategy",
    "metric_level",
    "total_revenue",
    "mean_daily_revenue",
    "mean_absolute_change",
    "price_std",
    "max_price_jump",
    "change_frequency",
]
EVALUATION_PAIRING_KEYS = [COL_STOCK_CODE, "invoice_day"]
EVALUATION_COMPARISONS = {
    "hybrid_vs_ml": ("hybrid", "ml"),
    "hybrid_vs_rule": ("hybrid", "rule"),
}
EVALUATION_PRODUCT_METRIC_LEVEL = "product"
EVALUATION_STRATEGY_METRIC_LEVEL = "strategy"
EVALUATION_METRIC_LEVELS = (EVALUATION_PRODUCT_METRIC_LEVEL, EVALUATION_STRATEGY_METRIC_LEVEL)
EVALUATION_SUMMARY_STOCK_CODE = "ALL"
EVALUATION_SUMMARY_SCHEMA = {
    "total_revenue": float,
    "mean_daily_revenue": float,
    "mean_absolute_change": float,
    "price_std": float,
    "max_price_jump": float,
    "change_frequency": float,
}
EVALUATION_TEST_SECTION_METRICS = {
    "revenue_tests": "predicted_revenue",
    "stability_tests": "abs_price_change",
}
EVALUATION_TEST_NAMES = ("paired_ttest", "wilcoxon")
EVALUATION_TESTS_SCHEMA = {
    "statistic": float,
    "p_value": float,
    "sample_size": int,
}


# -----------------------------
# Dashboard constants
# -----------------------------
DASHBOARD_SUMMARY_METRICS = (
    "total_revenue",
    "mean_daily_revenue",
    "mean_absolute_change",
    "price_std",
    "max_price_jump",
    "change_frequency",
)
DASHBOARD_PRIMARY_METRICS = (
    "total_revenue",
    "mean_absolute_change",
)
DASHBOARD_SUPPORTING_METRICS = tuple(
    metric_name for metric_name in DASHBOARD_SUMMARY_METRICS if metric_name not in DASHBOARD_PRIMARY_METRICS
)
DASHBOARD_STABILITY_SUPPORTING_METRICS = (
    "price_std",
    "max_price_jump",
    "change_frequency",
)
DASHBOARD_SECTION_TITLES = {
    "summary": "Section 1 - Overall Strategy Performance Comparison",
    "revenue": "Section 2 - Revenue Performance Analysis",
    "stability": "Section 3 - Pricing Stability Analysis",
    "statistical_tests": "Section 4 - Statistical Significance Tests",
    "product_comparison": "Section 5 - Supporting Product-Level Comparison",
    "distribution": "Section 6 - Supporting Distribution Analysis",
}
DASHBOARD_PRODUCT_METRIC_COLUMNS = [
    COL_STOCK_CODE,
    "strategy",
    "metric_level",
    *DASHBOARD_SUMMARY_METRICS,
]
DASHBOARD_PRODUCT_COMPARISON_METRICS = list(DASHBOARD_SUMMARY_METRICS)
DASHBOARD_STATISTICAL_TEST_LABELS = dict(EVALUATION_TEST_SECTION_METRICS)
DASHBOARD_TEST_LABELS = {
    "paired_ttest": "Paired t-test",
    "wilcoxon": "Wilcoxon signed-rank test",
}
DASHBOARD_SIGNIFICANCE_THRESHOLD = 0.05
DASHBOARD_HIGHLIGHT_BAR_COLOR = "#2F6B5F"
DASHBOARD_MUTED_BAR_COLOR = "#D8DEE6"
DASHBOARD_LEADER_CELL_STYLE = "background-color: #E9F7F2; font-weight: 600;"
DASHBOARD_SIGNIFICANT_CELL_STYLE = "background-color: #E9F7F2; color: #14532D; font-weight: 600;"
DASHBOARD_NONSIGNIFICANT_CELL_STYLE = "background-color: #FFF4E5; color: #9A3412; font-weight: 600;"
