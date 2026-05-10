# Comprehensive Implementation Notes

This document is a code-faithful, dissertation-oriented description of the current implementation in this repository. It is intentionally exhaustive. The aim is to capture not only the methodological flow, but also the concrete execution logic, frozen parameters, artifact schemas, data-contract rules, and current verified outputs that exist in the codebase and generated artifacts.

The description below reflects the implementation present on the current branch and the frozen outputs currently stored under `data/processed/`, `results/`, and `logs/`.

## 1. Study Objective and Implemented Scope

The project implements an offline comparative dynamic pricing study for a retail SME context. Three pricing strategies are implemented:

- Rule-based pricing
- Machine learning pricing
- Hybrid pricing

The comparison is deliberately scoped around two outcome dimensions:

- Revenue performance
- Pricing stability

The implementation is not a live pricing deployment system and is not a multi-model forecasting benchmark. Instead, the design fixes one demand model and one shared simulation environment so that strategy comparisons are made under identical demand predictions and identical candidate price sets.

The implemented analytical scope is:

- one source dataset slice
- one market
- five selected products
- daily product-level observations
- one frozen global linear regression demand model
- offline simulation using predicted demand

This means the implemented system is best understood as a reproducible experimental framework for comparative pricing analysis rather than a production pricing engine.

## 2. Data Source, Provenance, and Scope Boundaries

### 2.1 Original Data Source

The study uses the Online Retail II dataset. The original source file is an Excel workbook containing two worksheets:

- `2009-2010`
- `2010-2011`

Only the `2010-2011` worksheet is used in this project.

### 2.2 Raw Working File

The raw file used by the implementation is:

- `data/raw/online_retail_II_2010_2011.csv`

This CSV is treated as the immutable raw input.

### 2.3 Provenance Rules

The implementation treats the CSV as the raw system boundary. The following provenance assumptions are external to the codebase and are not programmatically verified:

- preserved the original worksheet column names
- did not remove rows
- did not apply filtering
- did not perform cleaning
- did not apply analytical transformations

This is important because the implementation separates raw data lineage from analytical preprocessing.

### 2.4 Scope Restrictions Implemented in Code

The current code enforces the following scope restrictions:

- Only the 2010-2011 worksheet export is used
- No 2009 data is used
- Only United Kingdom transactions are retained after cleaning
- Only five products are carried forward into modeling and simulation
- Aggregation is performed at daily product level
- The demand model is fixed to a single `LinearRegression` implementation

These restrictions are reflected in `config.py`, the preprocessing steps, and the downstream validators.

## 3. Environment and Dependency Stack

### 3.1 Runtime Assumptions

The codebase itself does not hard-code a specific environment manager or virtual-environment name. The implementation requires a Python environment that can import the pinned dependencies in `requirements.txt`.

If a virtual environment is used, one valid activation pattern is:

```bash
source venv/bin/activate
```

The exact interpreter invocation (`python`, `python3`, or a virtual-environment-local path) depends on the local environment rather than on repository logic.

### 3.2 Primary Libraries

The core implementation stack is:

- `pandas==2.3.3` for tabular processing
- `numpy==2.4.2` for numeric operations
- `pyarrow==23.0.1` for parquet I/O
- `scikit-learn==1.8.0` for the linear regression model
- `scipy==1.17.1` for paired t-tests and Wilcoxon tests
- `joblib==1.5.3` for model serialization
- `streamlit==1.54.0` for the dashboard
- `altair==6.0.0` for dashboard charts

The full pinned environment is stored in `requirements.txt`.

## 4. Repository Structure and Module Responsibilities

The implementation is organized into functional areas:

- `main.py`
  CLI entrypoint and top-level command dispatch.
- `config.py`
  Central source of paths, constants, schema definitions, strategy parameters, and reporting settings.
- `pipeline/`
  Execution naming and orchestration.
- `preprocessing/`
  Inspection, cleaning, product selection, aggregation, and feature engineering.
- `models/`
  Demand model training.
- `strategies/`
  Rule-based, ML, and hybrid price-selection logic.
- `simulation/`
  Shared simulation engine.
- `evaluation/`
  Metric computation and statistical testing.
- `dashboard/`
  Streamlit read-only comparison dashboard.
- `utils/`
  Logging configuration, data-contract enforcement, and simulation artifact loading.

## 5. Execution Model and CLI Behaviour

### 5.1 Main CLI

The executable entrypoint is `main.py`. It defines four explicit command families:

- `--run-pipeline`
- `--build`
- `--simulate`
- `--evaluate`
If no command is provided, the parser fails with:

- `Specify one of --run-pipeline, --build, --simulate, or --evaluate.`

There is no implicit default mode.

### 5.2 Command Precedence in `main.py`

The dispatch order in `main.py` is:

1. `--run-pipeline`
2. `--evaluate`
3. `--simulate`
4. `--build`

This precedence matters only if conflicting flags were ever passed simultaneously. Under normal usage, commands are expected to be explicit and non-conflicting.

### 5.3 Execution Naming in `config.py` and `pipeline/execution.py`

The current execution names are defined in `config.py` and exposed through helper accessors in `pipeline/execution.py`.

The current execution names are:

- Build group: `build`
- Units: `inspect`, `clean`, `select_products`, `aggregate_daily`, `feature_engineering`, `train_model`
- Commands: `simulate`, `evaluate`, `dashboard`

The build group currently contains exactly these six units in order:

1. `inspect`
2. `clean`
3. `select_products`
4. `aggregate_daily`
5. `feature_engineering`
6. `train_model`

### 5.4 Runner Behaviour in `pipeline/runner.py`

`pipeline/runner.py` provides:

- `run_build()` to execute the build group
- `run_simulation(strategy_name)` as an internal helper to run one strategy
- `run_all_simulations()` to iterate over `("rule", "ml", "hybrid")`
- `run_evaluation()` to run metric computation then statistical tests
- `run_unit(unit_name)` to dispatch individual units

Important execution details:

- `run_all_simulations()` wraps strategy failures and reports which strategy failed.
- `run_evaluation()` imports evaluation modules lazily inside the function.

### 5.5 Execution Modes

The implementation supports two practical ways to run the study:

- end-to-end with `python main.py --run-pipeline`
- step by step with `python main.py --build`, `python main.py --simulate`, and `python main.py --evaluate`

The step-by-step mode is useful when you want to inspect intermediate artifacts between stages or rerun only part of the workflow after a change.

### 5.6 Canonical Command Set

The intended command set is:

```bash
python main.py --run-pipeline
python main.py --build
python main.py --simulate
python main.py --evaluate
streamlit run dashboard/app.py
```

### 5.7 Stage Responsibilities

At a high level, each pipeline stage does the following:

- `--build`: runs the data preparation and model-training chain, which inspects the raw CSV, cleans it, selects products, aggregates daily product data, engineers features, and trains the demand model.
- `--simulate`: loads the trained model and test features, simulates all three pricing strategies (`rule`, `ml`, and `hybrid`), and writes candidate/result parquet files for each strategy.
- `--evaluate`: reads the simulation outputs, computes product-level and strategy-level metrics, and runs the paired statistical tests.
- `streamlit run dashboard/app.py`: opens the read-only dashboard that summarizes the evaluation artifacts.

### 5.8 Recommended End-to-End Order

The practical end-to-end execution options are:

1. `python main.py --run-pipeline`

or, equivalently:

1. `python main.py --build`
2. `python main.py --simulate`
3. `python main.py --evaluate`

Both paths build the processed data and model, produce all simulation outputs, and compute evaluation artifacts.

## 6. Configuration Architecture in `config.py`

`config.py` is the single source of truth for all shared implementation settings. The codebase is intentionally written so that step modules resolve paths and parameters from `config.py` rather than redefining them locally.

### 6.1 Path Configuration

Global project and path constants:

- `PROJECT_ROOT = "."`
- `RAW_DATA_PATH = "data/raw/"`
- `RAW_DATA_FILE = "online_retail_II_2010_2011.csv"`
- `PROCESSED_DATA_PATH = "data/processed/"`
- `RESULTS_PATH = "results/"`
- `LOGS_PATH = "logs/"`
- `REPORTS_PATH = "results/reports/"`

### 6.2 Processed Data Artifact Paths

- `CLEAN_DATA_PATH = "data/processed/clean_transactions.parquet"`
- `SELECTED_PRODUCTS_PATH = "data/processed/selected_products.parquet"`
- `DAILY_AGG_DATA_PATH = "data/processed/daily_product_data.parquet"`
- `FEATURE_TRAIN_DATA_PATH = "data/processed/feature_train_data.parquet"`
- `FEATURE_TEST_DATA_PATH = "data/processed/feature_test_data.parquet"`

### 6.3 Model Artifact Paths

- `MODEL_ARTIFACT_PATH = "models/artifacts/demand_model.joblib"`
- `MODEL_METRICS_PATH = "results/metrics/demand_model_metrics.json"`

### 6.4 Evaluation Artifact Paths

- `EVALUATION_STRATEGY_METRICS_PATH = "results/metrics/strategy_metrics.parquet"`
- `EVALUATION_STRATEGY_SUMMARY_PATH = "results/metrics/strategy_summary.json"`
- `EVALUATION_STATISTICAL_TESTS_PATH = "results/metrics/statistical_tests.json"`

### 6.5 Log File Names

- `BUILD_LOG_FILE = "build.log"`
- `SIMULATION_LOG_FILE = "simulate.log"`
- `EVALUATION_LOG_FILE = "evaluate.log"`
- `DASHBOARD_LOG_FILE = "dashboard.log"`
- `MASTER_LOG_FILE = "master.log"`

### 6.6 Raw Source Column Names

The raw CSV headers expected by the implementation are:

- `Invoice`
- `StockCode`
- `Description`
- `Quantity`
- `InvoiceDate`
- `Price`
- `Customer ID`
- `Country`

### 6.7 Canonical Processed Column Names

The canonical processed schema uses:

- `invoice`
- `stock_code`
- `description`
- `quantity`
- `invoice_date`
- `price`
- `customer_id`
- `country`

The raw-to-canonical mapping is:

| Raw column | Canonical column |
| --- | --- |
| `Invoice` | `invoice` |
| `StockCode` | `stock_code` |
| `Description` | `description` |
| `Quantity` | `quantity` |
| `InvoiceDate` | `invoice_date` |
| `Price` | `price` |
| `Customer ID` | `customer_id` |
| `Country` | `country` |

### 6.8 Cross-Domain Experimental Parameters

The major shared experimental constants are:

- `TRAIN_SPLIT_RATIO = 0.8`
- `PRICE_GRID_PERCENTAGE = 0.05`
- `SIMULATION_GRID_POINTS = 5`
- `RULE_PRICE_INCREASE = 0.02`
- `RULE_PRICE_DECREASE = 0.02`
- `MAX_DAILY_CHANGE = 0.03`
- `HYBRID_SMOOTHING_ALPHA = 0.3`

### 6.9 Cleaning Parameters

- `TARGET_COUNTRY = "United Kingdom"`
- `PRICE_OUTLIER_THRESHOLD = 1000.0`
- `PRICE_OUTLIER_REVIEW_TOP_N = 20`
- `INVOICE_CANCELLATION_PREFIX = "C"`
- `EXCLUDED_STOCK_CODES = ["DOS", "DOT", "POST", "M", "AMAZONFEE", "B"]`
- `CLEANING_PRICE_DESCRIBE_PERCENTILES = [0.5, 0.9, 0.95, 0.99, 0.995, 0.999]`

### 6.10 Product Selection Parameters

- `MIN_ACTIVE_DAYS = 150`
- `SELECTED_PRODUCT_COUNT = 5`
- `MIN_PRICE_STD = 0.0`

### 6.11 Model Parameters

- `MODEL_TYPE = "LinearRegression"`
- `MODEL_TARGET_COLUMN = "daily_units"`

### 6.12 Simulation Strategy Names

- `SIMULATION_STRATEGIES = ("rule", "ml", "hybrid")`

### 6.13 Evaluation Constants

The implementation freezes:

- the evaluation metric columns
- the pairing keys
- the supported pairwise comparisons
- the metric levels
- the summary row stock-code sentinel
- the JSON schema of summary metrics and statistical tests

The current comparisons are:

- `hybrid_vs_ml`
- `hybrid_vs_rule`

The current pairing keys are:

- `stock_code`
- `invoice_day`

### 6.14 Dashboard Constants

The dashboard uses:

- the six summary metrics
- the primary dissertation metrics:
  - `total_revenue`
  - `mean_absolute_change`
- the supporting dashboard metrics:
  - `mean_daily_revenue`
  - `price_std`
  - `max_price_jump`
  - `change_frequency`
- the supporting stability metrics:
  - `price_std`
  - `max_price_jump`
  - `change_frequency`
- section-title constants for the five dashboard sections
- product-level metric columns
- a significance threshold of `0.05`
- label maps for test names and statistical sections
- dashboard highlight colors and table-cell style strings used for visual emphasis

## 7. Shared Helper Utilities

### 7.1 Path Resolution in `preprocessing/common.py`

The project uses shared helper functions to keep file resolution consistent:

- `configured_root(project_root)`
- `configured_path(project_root, relative_path)`
- `configured_path_from_map(project_root, path_map, key)`

These ensure all step modules resolve paths relative to `PROJECT_ROOT`.

### 7.2 Required-Column Checking

`ensure_required_columns(df, required_columns, context)` checks that all required columns are present. If not, it raises a `ValueError` naming the missing columns and the failing context.

This function is reused across preprocessing, modeling, simulation, and evaluation.

## 8. Logging Architecture

### 8.1 Logging Entry Behaviour

`utils/logging_config.py` defines `configure_logging()`. When invoked:

- the root logger is set to `INFO`
- any existing handlers are cleared
- `logs/` is created if missing
- a `master.log` handler is always added
- target-specific handlers are added for the selected command

### 8.2 Log Formats

Two formats are used:

- `master.log`
  - `%(asctime)s - %(levelname)s - %(message)s`
- target log files
  - `%(asctime)s | %(levelname)s | %(message)s`

### 8.3 Prefix-Based Filtering

Target-specific logs use `LoggerPrefixFilter`, which filters records by logger name prefixes. This keeps, for example, `logs/simulate.log` limited to logs emitted from `simulation.simulator`.

### 8.4 Logging Target Map

Current logging targets are:

- build -> `preprocessing.raw_inspection`, `preprocessing.clean_data`, `preprocessing.select_products`, `preprocessing.aggregate_daily`, `preprocessing.feature_engineering`, `models.demand_model`
- simulation -> `simulation.simulator`
- evaluation -> `evaluation.metrics`, `evaluation.statistical_tests`, `utils.simulation_artifacts`
- dashboard -> `dashboard.app`

This logging arrangement is useful for dissertation auditability because each pipeline stage leaves a stage-specific execution trail in addition to the global `master.log`.

## 9. Data Inspection Implementation

### 9.1 Module and Outputs

Inspection is implemented in:

- `preprocessing/raw_inspection.py`

Outputs:

- `results/reports/raw_inspection_report.json`
- `logs/build.log`

### 9.2 Inspection Responsibilities

The inspection step:

- loads the raw CSV
- records dataset shape
- records raw dtypes
- computes null counts and percentages
- counts cancellation rows using invoices starting with `C`
- computes descriptive statistics for `Quantity`
- computes descriptive statistics for `Price`
- counts negative and zero quantities
- counts negative and zero prices
- records country distribution
- computes revenue by country using `Quantity * Price`
- attempts datetime parsing for `InvoiceDate`
- stores downstream frozen cleaning decisions

### 9.3 Inspection Report Payload Structure

The report payload currently contains:

- `step`
- `name`
- `source_file`
- `dataset_shape`
- `column_types`
- `null_summary`
- `cancellation_summary`
- `quantity_distribution`
- `quantity_quality_flags`
- `price_distribution`
- `price_quality_flags`
- `country_distribution_top20`
- `revenue_by_country_top20`
- `date_range_validation`
- `frozen_decisions_for_next_step`

### 9.4 Current Frozen Inspection Findings

From `results/reports/raw_inspection_report.json`, the current raw dataset profile is:

- Rows: `541,910`
- Columns: `8`
- Source file: `/home/shraddha/Documents/Projects/dynamic_pricing_study/data/raw/online_retail_II_2010_2011.csv`

Current raw dtypes are:

| Column | Raw dtype |
| --- | --- |
| `Invoice` | `object` |
| `StockCode` | `object` |
| `Description` | `object` |
| `Quantity` | `int64` |
| `InvoiceDate` | `object` |
| `Price` | `float64` |
| `Customer ID` | `float64` |
| `Country` | `object` |

Current null profile includes:

- `Customer ID`: `135,080` nulls (`24.9266%`)
- `Description`: `1,454` nulls (`0.2683%`)
- all other raw columns: `0` nulls

Quality flags in the inspection artifact are:

- cancellations: `9,288`
- negative quantity rows: `10,624`
- zero quantity rows: `0`
- negative price rows: `2`
- zero price rows: `2,515`

Current raw quantity descriptive landmarks:

- minimum quantity: `-80,995`
- median quantity: `3`
- 95th percentile quantity: `29`
- 99th percentile quantity: `100`
- maximum quantity: `80,995`

Current raw price descriptive landmarks:

- minimum price: `-11,062.06`
- median price: `2.08`
- 95th percentile price: `9.95`
- 99th percentile price: `18.0`
- maximum price: `38,970.0`

Current parsed raw date range:

- minimum date: `2010-12-01 08:26:00`
- maximum date: `2011-12-09 12:50:00`

Current top country by row count:

- `United Kingdom`: `495,478` rows

### 9.5 Inspection Outcome

The current inspection step stores the following frozen downstream decisions:

- Keep UK only
- Remove cancelled invoices
- Remove negative quantities
- Remove zero or negative prices
- Temporal boundary already fixed at source (2010-2011 only)

Inspection is descriptive only. No downstream module consumes the raw inspection report as a computational input, but it is the evidence base for the cleaning rules.

## 10. Cleaning Implementation

### 10.1 Module and Output

Cleaning is implemented in:

- `preprocessing/clean_data.py`

Outputs:

- `data/processed/clean_transactions.parquet`
- `logs/build.log`

### 10.2 Raw Column Validation

Before any transformation, cleaning checks the presence of these required raw columns:

- `Invoice`
- `StockCode`
- `Description`
- `Quantity`
- `InvoiceDate`
- `Price`
- `Customer ID`
- `Country`

### 10.3 Canonicalization and String Standardization

The raw dataframe is renamed using `RAW_TO_CANONICAL_COLUMNS`, producing the canonical processed schema.

String handling then applies:

- cast configured string columns to pandas `string`
- trim surrounding whitespace
- uppercase `invoice`
- uppercase `stock_code`
- collapse repeated whitespace in `description`
- trim `description` again

### 10.4 Type Coercion Logic

The cleaning step then coerces:

- `quantity` using `pd.to_numeric(errors="coerce")`
- `price` using `pd.to_numeric(errors="coerce")`
- `invoice_date` using `pd.to_datetime(errors="coerce", format="mixed")`
- `customer_id` using `pd.to_numeric(errors="coerce")` and then `Int64`

Rows with non-numeric quantities, non-numeric prices, or unparseable dates would be dropped. In the current frozen run, no such drops were logged before the filtering stages.

### 10.5 Deterministic Filtering Sequence

The filtering sequence is:

1. restrict to `country == "United Kingdom"` after case-normalized comparison
2. remove invoices starting with `C`
3. remove rows with `quantity < 0`
4. remove rows with `price <= 0`
5. remove rows whose `stock_code` is in `EXCLUDED_STOCK_CODES`
6. inspect positive-price distribution
7. remove rows with `price > 1000.0`
8. run quality checks
9. run exact-schema validation via `validate_clean_transactions`

### 10.6 Important Detail About Row Counts

The row counts removed at each cleaning stage are conditional on earlier filters. For example:

- raw inspection found `9,288` cancellation rows in the entire raw dataset
- cleaning removed `7,856` cancelled rows after restricting to United Kingdom first

The same applies to negative quantities and non-positive prices. Therefore, inspection counts and cleaning-removal counts are not expected to match exactly.

### 10.7 Current Cleaning Log Summary

From `logs/build.log`, the current stagewise counts are:

| Cleaning stage | Rows removed | Rows remaining |
| --- | ---: | ---: |
| Initial raw rows | 0 | 541,910 |
| Remove non-UK rows | 46,432 | 495,478 |
| Remove cancelled invoice rows | 7,856 | 487,622 |
| Remove negative-quantity rows | 1,336 | 486,286 |
| Remove non-positive-price rows | 1,163 | 485,123 |
| Remove non-product service-code rows | 1,041 | 484,082 |
| Remove price outliers above GBP 1000 | 0 | 484,082 |

### 10.8 Positive Price Distribution After Earlier Filters

The logged positive-price distribution after the earlier cleaning filters is:

- minimum: `0.0010`
- median: `2.1000`
- 95th percentile: `9.9500`
- 99th percentile: `16.6300`
- maximum: `649.5000`

The maximum value being below the configured threshold explains why zero rows were removed by the final outlier filter in the current frozen run.

### 10.9 Quality Checks Performed

Cleaning enforces:

- all remaining `country` values equal `United Kingdom`
- no remaining negative quantities
- no remaining non-positive prices
- no remaining prices above `1000.0`
- no remaining excluded service stock codes
- no nulls in required non-null columns

### 10.10 Cleaned Output Schema

The exact frozen cleaned output column order is:

1. `invoice`
2. `stock_code`
3. `description`
4. `quantity`
5. `invoice_date`
6. `price`
7. `customer_id`
8. `country`

### 10.11 Cleaned Dataset Validation Rules

`validate_clean_transactions()` requires:

- exact column order matching the frozen schema
- non-empty dataset
- all `country` values equal target country
- no negative quantity
- no non-positive price
- no price above the outlier threshold

### 10.12 Current Frozen Cleaned Dataset Facts

The current cleaned dataset has:

- rows: `484,082`
- columns: `8`
- unique stock codes: `3,801`
- minimum invoice timestamp: `2010-12-01 08:26:00`
- maximum invoice timestamp: `2011-12-09 12:49:00`

## 11. Product Selection Implementation

### 11.1 Module and Outputs

Product selection is implemented in:

- `preprocessing/select_products.py`

Outputs:

- `data/processed/selected_products.parquet`
- `results/reports/product_selection_report.json`
- `logs/build.log`

### 11.2 Input Requirements

The cleaned dataset must contain:

- `stock_code`
- `description`
- `invoice_date`
- `price`
- `quantity`

### 11.3 Pre-Selection Logic

The step:

- loads the cleaned parquet
- re-parses `invoice_date`
- drops any rows with invalid dates if they occur
- creates `invoice_day = invoice_date.dt.date`
- creates `revenue_line = price * quantity`

### 11.4 Product-Level Metrics Computed

For each `stock_code`, the implementation computes:

- `revenue` as the sum of `revenue_line`
- `price_std` as the standard deviation of `price`
- `active_days` as the number of unique `invoice_day` values

### 11.5 Eligibility Filters

The current eligibility filters are:

- `price_std > 0.0`
- `active_days >= 150`

### 11.6 Ranking and Description Assignment

Eligible products are sorted by `revenue` descending, and the top `5` are selected.

Descriptions are assigned using `_build_description_map()`, which:

- removes null or blank descriptions
- groups by `stock_code`
- assigns the mode of the descriptions for that code

This is a robustness detail: if a stock code has minor textual variations in `description`, the implementation uses the most frequent description rather than the first seen description.

### 11.7 Product Selection Report Payload

The report JSON contains:

- `step`
- `name`
- `selection_parameters`
- `run_summary`
- `selected_products`

### 11.8 Selected Products Dataset Schema

The exact frozen schema is:

1. `stock_code`
2. `description`
3. `revenue`
4. `price_std`
5. `active_days`

### 11.9 Selected Products Validation Rules

`validate_selected_products()` requires:

- exact column order
- non-empty dataset
- exactly `5` rows
- non-null, non-blank `stock_code` values

### 11.10 Current Frozen Selection Results

From the current report artifact and logs:

- products analyzed: `3,801`
- eligible products: `484`
- selected products: `5`

The current frozen product universe is:

| Stock code | Description | Revenue | Price std | Active days |
| --- | --- | ---: | ---: | ---: |
| `22423` | REGENCY CAKESTAND 3 TIER | 142273.29 | 4.5361392367 | 301 |
| `85123A` | WHITE HANGING HEART T-LIGHT HOLDER | 100676.23 | 1.0086196376 | 305 |
| `47566` | PARTY BUNTING | 93658.53 | 2.1793744767 | 291 |
| `85099B` | JUMBO BAG RED RETROSPOT | 86471.34 | 0.9151869223 | 300 |
| `22086` | PAPER CHAIN KIT 50'S CHRISTMAS | 62742.54 | 1.1454285635 | 161 |

## 12. Daily Aggregation Implementation

### 12.1 Module and Output

Aggregation is implemented in:

- `preprocessing/aggregate_daily.py`

Outputs:

- `data/processed/daily_product_data.parquet`
- `logs/build.log`

### 12.2 Input Requirements

Inputs are:

- cleaned transactions parquet
- selected products parquet

The selected-products parquet is validated before use.

### 12.3 Aggregation Logic

The step:

- loads selected products
- standardizes selected stock codes to uppercase trimmed strings
- loads cleaned transactions
- filters the cleaned data to the selected stock codes
- parses `invoice_date`
- creates `invoice_day` using `.dt.normalize()`
- computes `revenue_line = quantity * price`
- groups by `(stock_code, invoice_day)`

No calendar completion or zero-filling is performed for missing dates. The aggregated dataset therefore contains only product-day combinations that are present in the cleaned transactional data.

The grouped outputs are:

- `daily_units = sum(quantity)`
- `avg_daily_price = mean(price)`
- `daily_revenue = sum(revenue_line)`

Rows are then sorted by:

- `stock_code`
- `invoice_day`

using stable `mergesort`.

### 12.4 Aggregation Output Schema

The exact frozen column order is:

1. `stock_code`
2. `invoice_day`
3. `daily_units`
4. `avg_daily_price`
5. `daily_revenue`

### 12.5 Aggregation Validation Rules

`validate_daily_aggregation()` requires:

- exact column order
- non-empty dataset
- no null `stock_code`
- no null `invoice_day`

### 12.6 Current Frozen Aggregation Results

From `logs/build.log`, the current aggregation summary is:

- cleaned input rows: `484,082`
- rows belonging to selected products: `8,680`
- aggregated output rows: `1,358`
- products: `5`
- date range: `2010-12-01` to `2011-12-09`

Per-product daily row counts in the frozen aggregated table are:

| Stock code | Daily rows |
| --- | ---: |
| `22086` | 161 |
| `22423` | 301 |
| `47566` | 291 |
| `85099B` | 300 |
| `85123A` | 305 |

## 13. Feature Engineering Implementation

### 13.1 Module and Outputs

Feature engineering is implemented in:

- `preprocessing/feature_engineering.py`

Outputs:

- `data/processed/feature_train_data.parquet`
- `data/processed/feature_test_data.parquet`
- `logs/build.log`

### 13.2 Input Requirements

The daily aggregated dataset must contain:

- `stock_code`
- `invoice_day`
- `daily_units`
- `avg_daily_price`
- `daily_revenue`

### 13.3 Feature Construction Logic

Feature engineering proceeds in this order:

1. parse `invoice_day`
2. sort by `(stock_code, invoice_day)` using stable `mergesort`
3. compute lagged and rolling demand features within each product
4. compute weekday and month variables
5. one-hot encode weekday and month
6. add any missing one-hot columns as zeros so the schema is fixed
7. drop rows missing required lag features
8. split chronologically per product into train and test
9. sort train and test outputs again by `(stock_code, invoice_day)`
10. validate both outputs against the frozen schema

### 13.4 Demand History Features

Within each `stock_code` group:

- `lag1_units` is `daily_units.shift(1)`
- `lag7_units` is `daily_units.shift(7)`
- `rolling7_mean_units` is the mean of the previous 7 retained observations in that product's aggregated series, excluding the current row, implemented as:
  - `grouped_units.shift(1).rolling(window=7, min_periods=7).mean()`

Because the daily aggregation step does not insert missing calendar dates, these lag and rolling features operate over prior observed product-day rows rather than over a gap-filled daily calendar. Each retained modeled row therefore requires enough prior observed rows to populate all three lag-related fields.

### 13.5 Calendar Features

Calendar variables are:

- `weekday = invoice_day.dt.weekday`
- `month = invoice_day.dt.month`

One-hot columns are then generated for:

- weekdays `0` through `6`
- months `1` through `12`

The code explicitly inserts zero-filled dummy columns if a weekday or month is absent in the observed data so that the output schema remains fixed across reruns.

### 13.6 Train/Test Split Logic

The split is performed separately for each product:

- data is sorted chronologically within the product
- `split_idx = int(len(product_df) * 0.8)`
- rows before the split go to train
- rows at and after the split go to test

The implementation raises an error if a split would make either side empty.

There is no shuffling.

### 13.7 Feature Output Schema

The exact frozen feature schema contains 29 columns in this order:

1. `stock_code`
2. `invoice_day`
3. `daily_units`
4. `avg_daily_price`
5. `daily_revenue`
6. `lag1_units`
7. `lag7_units`
8. `rolling7_mean_units`
9. `weekday`
10. `month`
11. `weekday_0`
12. `weekday_1`
13. `weekday_2`
14. `weekday_3`
15. `weekday_4`
16. `weekday_5`
17. `weekday_6`
18. `month_1`
19. `month_2`
20. `month_3`
21. `month_4`
22. `month_5`
23. `month_6`
24. `month_7`
25. `month_8`
26. `month_9`
27. `month_10`
28. `month_11`
29. `month_12`

### 13.8 Frozen Model Feature Vector

The demand model uses these 23 predictors:

1. `lag1_units`
2. `lag7_units`
3. `rolling7_mean_units`
4. `avg_daily_price`
5. `weekday_0`
6. `weekday_1`
7. `weekday_2`
8. `weekday_3`
9. `weekday_4`
10. `weekday_5`
11. `weekday_6`
12. `month_1`
13. `month_2`
14. `month_3`
15. `month_4`
16. `month_5`
17. `month_6`
18. `month_7`
19. `month_8`
20. `month_9`
21. `month_10`
22. `month_11`
23. `month_12`

### 13.9 Feature Validation Rules

`validate_feature_data()` requires:

- exact 29-column schema
- non-empty dataset
- no null `stock_code`
- no null `invoice_day`
- no null values in `daily_units`, `lag1_units`, `lag7_units`, or `rolling7_mean_units`
- no negative values in those same demand fields
- each row has weekday one-hot columns summing to `1`
- each row has month one-hot columns summing to `1`
- all frozen model feature columns are present

### 13.10 Current Frozen Feature Results

From `logs/build.log` and the generated artifacts:

- aggregated input rows: `1,358`
- modeled rows after lag-based row removal: `1,323`
- training rows: `1,057`
- test rows: `266`
- products: `5`
- columns per split: `29`

Current per-product split sizes are:

| Stock code | Train rows | Test rows |
| --- | ---: | ---: |
| `22086` | 123 | 31 |
| `22423` | 235 | 59 |
| `47566` | 227 | 57 |
| `85099B` | 234 | 59 |
| `85123A` | 238 | 60 |

## 14. Demand Model Training Implementation

### 14.1 Module and Outputs

Model training is implemented in:

- `models/demand_model.py`

Outputs:

- `models/artifacts/demand_model.joblib`
- `results/metrics/demand_model_metrics.json`
- `logs/build.log`

### 14.2 Input Validation

The train and test feature datasets are validated before fitting. Validation includes:

- full feature-schema validation via `validate_feature_data()`
- presence of all 23 feature columns plus the target column `daily_units`
- failure if any of those required fields contain null values

### 14.3 Model Type

The fitted model is:

- `sklearn.linear_model.LinearRegression`

No alternative model implementations are currently present in the training pipeline.

### 14.4 Training and Evaluation Procedure

The model training step:

- loads train and test parquet files
- extracts `x_train`, `y_train`, `x_test`, `y_test`
- fits `LinearRegression()` on `x_train`
- predicts on `x_test`
- computes:
  - mean absolute error
  - root mean squared error
  - R-squared
- serializes the trained estimator with `joblib.dump`
- writes metrics to JSON

### 14.5 Current Frozen Model Metrics

From `results/metrics/demand_model_metrics.json` and `logs/build.log`, the current model metrics are:

- model type: `LinearRegression`
- target: `daily_units`
- train rows: `1,057`
- test rows: `266`
- MAE: `203.98369661531677`
- RMSE: `269.8076731882339`
- R-squared: `-1.147905626166002`

Rounded presentation values:

- MAE: `203.9837`
- RMSE: `269.8077`
- R-squared: `-1.1479`

### 14.6 Current Frozen Coefficients

The current saved linear model has:

- intercept: `137.97799338611006`

Feature coefficients:

| Feature | Coefficient |
| --- | ---: |
| `lag1_units` | -0.030819713585271153 |
| `lag7_units` | -0.04451092069492718 |
| `rolling7_mean_units` | 0.25198080752327895 |
| `avg_daily_price` | -6.2911506909228825 |
| `weekday_0` | 9.989426013404199 |
| `weekday_1` | 28.534327454360838 |
| `weekday_2` | 0.8639408004399678 |
| `weekday_3` | 17.920352438333502 |
| `weekday_4` | -8.677911873714892 |
| `weekday_5` | approximately 0 (`-1.7053025658242404e-13`) |
| `weekday_6` | -48.63013483282355 |
| `month_1` | -25.177738346332802 |
| `month_2` | -46.61815654632982 |
| `month_3` | -26.517230783316272 |
| `month_4` | -17.739095897189248 |
| `month_5` | -5.447485698655004 |
| `month_6` | -43.01115533547764 |
| `month_7` | -29.454477870983947 |
| `month_8` | -39.977986397711774 |
| `month_9` | -36.5804883183742 |
| `month_10` | -14.675045129535082 |
| `month_11` | 319.97711508003323 |
| `month_12` | -34.778254756127446 |

These coefficients are part of the frozen implementation state and can be cited if coefficient interpretability is needed, though the poor predictive performance means they should not be over-interpreted causally.

## 15. Strategy Layer

Three strategy modules expose `choose_price(candidate_table, context)`.

### 15.1 Shared Expectations Across Strategies

All strategies assume:

- `candidate_table` is non-empty
- the simulator has already computed `predicted_demand` and `predicted_revenue` for each candidate price
- price selection must occur from the simulator's candidate grid, not from arbitrary continuous prices

### 15.2 Rule-Based Strategy

Implemented in:

- `strategies/rule_based.py`

#### Core logic

The rule-based strategy:

1. obtains `base_price` from the simulation context
2. reads the current row's `rolling7_mean_units`
3. looks up predicted demand at the base price candidate
4. compares predicted base-price demand with the rolling mean
5. sets a target price:
   - `base_price * 1.02` if predicted demand is above rolling mean
   - `base_price * 0.98` if predicted demand is below rolling mean
   - `base_price` if equal
6. selects the closest available candidate price to that target

#### Fallback detail

If the candidate table does not contain a candidate exactly equal to `base_price`, the strategy uses the nearest available candidate to estimate `base_predicted_demand`. In the current simulation design, the base price is included in the grid because there are 5 evenly spaced points over a symmetric range, but the fallback still exists.

#### Tie-breaking

Candidate choice is ranked by:

1. smallest distance to target price
2. smallest distance to base price
3. lower candidate price

### 15.3 Machine Learning Strategy

Implemented in:

- `strategies/ml_pricing.py`

#### Core logic

The ML strategy is the unconstrained optimizer. It ranks candidates by:

1. highest `predicted_revenue`
2. smallest distance to the base price
3. lower candidate price

It then returns the top-ranked candidate price.

This strategy has no inter-day stability control.

### 15.4 Hybrid Strategy

Implemented in:

- `strategies/hybrid_pricing.py`

#### Core logic

The hybrid strategy:

1. computes the ML-optimal price using the same ranking logic as the ML strategy
2. computes a clamp interval around `previous_price`
3. clips the ML-optimal price to that interval
4. smooths the clamped price toward the previous price
5. projects the smoothed value back to the nearest candidate price

The clamp interval is:

- lower bound: `previous_price * (1 - MAX_DAILY_CHANGE)`
- upper bound: `previous_price * (1 + MAX_DAILY_CHANGE)`

With current default parameters:

- lower bound: `previous_price * 0.97`
- upper bound: `previous_price * 1.03`

The smoothing equation is:

- `smoothed_price = HYBRID_SMOOTHING_ALPHA * clamped_price + (1 - HYBRID_SMOOTHING_ALPHA) * previous_price`

With current default `HYBRID_SMOOTHING_ALPHA = 0.3`, this becomes:

- `smoothed_price = 0.3 * clamped_price + 0.7 * previous_price`

#### Final projection tie-breaking

The final projection back to the candidate grid ranks candidates by:

1. smallest distance to `smoothed_price`
2. smallest distance to `base_price`
3. lower candidate price

#### Stateful property

Unlike the other two strategies, the hybrid strategy requires `previous_price` in the context. This makes it sequential and path-dependent at the product level.

## 16. Shared Simulation Engine

### 16.1 Module and Outputs

Simulation is implemented in:

- `simulation/simulator.py`

For each strategy, it writes:

- candidate table parquet
- result table parquet

Current configured paths are:

| Strategy | Candidate output | Result output |
| --- | --- | --- |
| `rule` | `results/simulation/rule_candidates.parquet` | `results/simulation/rule_results.parquet` |
| `ml` | `results/simulation/ml_candidates.parquet` | `results/simulation/ml_results.parquet` |
| `hybrid` | `results/simulation/hybrid_candidates.parquet` | `results/simulation/hybrid_results.parquet` |

### 16.2 Simulation Inputs

Simulation requires:

- `data/processed/feature_test_data.parquet`
- `models/artifacts/demand_model.joblib`

The test feature dataset must contain:

- `invoice_day`
- `stock_code`
- `avg_daily_price`
- all 23 model feature columns

### 16.3 Candidate Grid Construction

Candidate prices are created by:

- `low = base_price * (1 - 0.05)`
- `high = base_price * (1 + 0.05)`
- `np.linspace(low, high, 5)`

Therefore, the five candidate multipliers are exactly:

- `0.95`
- `0.975`
- `1.00`
- `1.025`
- `1.05`

Because the grid has an odd number of evenly spaced points around the base price, the base price itself is included.

### 16.4 Candidate Prediction Logic

For each candidate price:

- a feature row is copied from the current test row
- `avg_daily_price` is replaced with the candidate price
- the frozen linear model predicts demand
- predicted demand is clipped at zero from below
- predicted revenue is computed as `candidate_price * predicted_demand`

### 16.5 Candidate Table Schema

The exact candidate schema is:

1. `invoice_day`
2. `stock_code`
3. `candidate_price`
4. `predicted_demand`
5. `predicted_revenue`
6. `candidate_rank_by_revenue`

### 16.6 Result Table Schema

The exact simulation result schema is:

1. `invoice_day`
2. `stock_code`
3. `base_price`
4. `previous_price`
5. `chosen_price`
6. `price_change`
7. `abs_price_change`
8. `predicted_demand`
9. `predicted_revenue`
10. `strategy_name`

### 16.7 Strategy Context

The simulator builds a context dictionary containing:

- `base_price`
- `row`
- `strategy_name`

For the hybrid strategy it also adds:

- `previous_price`

The context keys are explicitly checked against expected key sets.

### 16.8 Previous Price Initialization

The simulator tracks `previous_price_by_product`. For each product:

- if no previous chosen price exists yet, `previous_price = base_price`
- otherwise, `previous_price` is the last chosen price for that product

This means each product's simulation trajectory is sequential within the test period.

### 16.9 Chosen-Candidate Resolution

After a strategy returns a price:

- if that exact candidate price exists, its row is selected
- otherwise, the simulator falls back to the nearest candidate price

### 16.10 Result Record Construction

The simulator records:

- `price_change = chosen_price - previous_price`
- `abs_price_change = abs(price_change)`
- `predicted_demand` and `predicted_revenue` from the chosen candidate row

### 16.11 Candidate Validation Rules

`validate_simulation_candidates()` requires:

- exact candidate schema
- non-empty dataset
- no null `invoice_day`
- no null `stock_code`
- all `candidate_price > 0`
- all `predicted_demand >= 0`
- all `predicted_revenue >= 0`
- all `candidate_rank_by_revenue >= 1`

### 16.12 Result Validation Rules

`validate_simulation_results()` requires:

- exact result schema
- non-empty dataset
- no null `invoice_day`
- no null `stock_code`
- all `base_price > 0`
- all `chosen_price > 0`
- all `previous_price > 0`
- `price_change` must equal `chosen_price - previous_price`
- `abs_price_change` must equal `abs(price_change)`
- `abs_price_change >= 0`
- `predicted_demand >= 0`
- `predicted_revenue >= 0`

### 16.13 Current Frozen Simulation Output Sizes

From `logs/simulate.log` and the parquet files:

- test rows per strategy: `266`
- candidate rows per strategy: `1,330`
- result rows per strategy: `266`

The candidate count is exactly:

- `266 x 5 = 1,330`

### 16.14 Example of Hybrid Sequential Behaviour

The current frozen `hybrid_results.parquet` shows the sequential nature of the hybrid policy. For stock code `22086`, the first observed test row uses:

- `base_price = 3.460000`
- `previous_price = 3.460000`
- `chosen_price = 3.460000`

On the next test row for the same product:

- `base_price = 2.910000`
- `previous_price = 3.460000`
- `chosen_price = 3.055500`

This illustrates that the hybrid strategy is constrained by the previous chosen price rather than acting independently on each row.

## 17. Evaluation Metrics Implementation

### 17.1 Module and Outputs

Evaluation metrics are implemented in:

- `evaluation/metrics.py`

Outputs:

- `results/metrics/strategy_metrics.parquet`
- `results/metrics/strategy_summary.json`
- `logs/evaluate.log`

### 17.2 Simulation Output Loading

Evaluation does not directly read arbitrary files from `results/simulation/`. Instead, it uses `utils/simulation_artifacts.py`.

That utility:

- confirms all required result files exist
- loads each strategy result parquet
- validates each with `validate_simulation_results()`
- confirms the `strategy_name` column matches the expected strategy
- checks that there are no duplicate `(stock_code, invoice_day)` pairs
- sorts the results by the evaluation pairing keys

### 17.3 Product-Level Metric Formulas

Product-level metrics are computed per `(strategy_name, stock_code)`:

- `total_revenue = sum(predicted_revenue)`
- `mean_daily_revenue = mean(predicted_revenue)`
- `mean_absolute_change = mean(abs_price_change)`
- `max_price_jump = max(abs_price_change)`
- `change_frequency = mean(price_change != 0)`
- `price_std = std(chosen_price, ddof=0)`

The product-level rows are then relabeled from `strategy_name` to `strategy` and assigned:

- `metric_level = "product"`

### 17.4 Strategy-Level Metric Formulas

Strategy-level metrics are aggregated from product-level rows:

- `total_revenue = sum(product total_revenue)`
- `mean_daily_revenue = mean(product mean_daily_revenue)`
- `mean_absolute_change = mean(product mean_absolute_change)`
- `price_std = mean(product price_std)`
- `max_price_jump = max(product max_price_jump)`
- `change_frequency = mean(product change_frequency)`

Strategy summary rows use:

- `stock_code = "ALL"`
- `metric_level = "strategy"`

### 17.5 Evaluation Metrics Output Schema

The exact evaluation metrics schema is:

1. `stock_code`
2. `strategy`
3. `metric_level`
4. `total_revenue`
5. `mean_daily_revenue`
6. `mean_absolute_change`
7. `price_std`
8. `max_price_jump`
9. `change_frequency`

### 17.6 Evaluation Summary JSON Schema

The strategy summary JSON is a mapping from strategy name to:

- `total_revenue` as float
- `mean_daily_revenue` as float
- `mean_absolute_change` as float
- `price_std` as float
- `max_price_jump` as float
- `change_frequency` as float

### 17.7 Evaluation Metrics Validation Rules

`validate_evaluation_metrics()` requires:

- exact column order
- non-empty dataset
- non-null `stock_code`
- non-null, non-blank `strategy`
- exact strategy set equal to `{"rule", "ml", "hybrid"}`
- exact metric-level set equal to `{"product", "strategy"}`
- no null values in summary metric columns

### 17.8 Current Frozen Evaluation Results

From the current `strategy_metrics.parquet` and `strategy_summary.json`:

There are:

- `15` product-level rows
- `3` strategy-level rows
- `18` total rows

Current strategy-level summary:

| Strategy | Total revenue | Mean daily revenue | Mean abs change | Price std | Max price jump | Change frequency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `hybrid` | 378588.42467631155 | 1413.6257208241577 | 0.7599901254026927 | 0.8026869279726642 | 6.728 | 0.9245564156427154 |
| `ml` | 393990.38449901843 | 1470.9645987269578 | 1.1387687130798765 | 1.0346272395886509 | 8.816999999999998 | 0.9480196253345227 |
| `rule` | 384707.66064544633 | 1436.0419674174232 | 1.127264443365309 | 1.0126596939143908 | 8.607071428571427 | 0.9514094558429973 |

Rounded presentation values:

| Strategy | Total revenue | Mean daily revenue | Mean abs change | Price std | Max price jump | Change frequency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `hybrid` | 378588.4247 | 1413.6257 | 0.7600 | 0.8027 | 6.7280 | 0.9246 |
| `ml` | 393990.3845 | 1470.9646 | 1.1388 | 1.0346 | 8.8170 | 0.9480 |
| `rule` | 384707.6606 | 1436.0420 | 1.1273 | 1.0127 | 8.6071 | 0.9514 |

### 17.9 Product-Level Results

Current product-level metrics are:

| Stock code | Strategy | Total revenue | Mean daily revenue | Mean abs change | Price std | Max price jump | Change frequency |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `22086` | `hybrid` | 40213.257452 | 1297.201853 | 0.134818 | 0.233344 | 0.920145 | 0.967742 |
| `22423` | `hybrid` | 160060.368854 | 2712.887608 | 1.947367 | 1.981776 | 6.728000 | 0.949153 |
| `47566` | `hybrid` | 85093.394301 | 1492.866567 | 1.236288 | 1.233002 | 5.473000 | 0.807018 |
| `85099B` | `hybrid` | 40648.080539 | 688.950518 | 0.211860 | 0.244504 | 0.854273 | 0.932203 |
| `85123A` | `hybrid` | 52573.323530 | 876.222059 | 0.269618 | 0.320808 | 1.253500 | 0.966667 |
| `22086` | `ml` | 41810.734317 | 1348.733365 | 0.304290 | 0.312736 | 1.108579 | 1.000000 |
| `22423` | `ml` | 166080.898117 | 2814.930477 | 2.834161 | 2.605811 | 8.817000 | 0.983051 |
| `47566` | `ml` | 88305.187027 | 1549.213807 | 1.717255 | 1.496009 | 6.552000 | 0.824561 |
| `85099B` | `ml` | 42666.182364 | 723.155633 | 0.356446 | 0.323826 | 1.174091 | 0.949153 |
| `85123A` | `ml` | 55127.382675 | 918.789711 | 0.481692 | 0.434754 | 1.711500 | 0.983333 |
| `22086` | `rule` | 40727.172221 | 1313.779749 | 0.295964 | 0.300132 | 1.029395 | 1.000000 |
| `22423` | `rule` | 162201.589997 | 2749.179491 | 2.832346 | 2.505886 | 8.607071 | 0.983051 |
| `47566` | `rule` | 86528.829778 | 1518.049645 | 1.681372 | 1.511610 | 6.396000 | 0.824561 |
| `85099B` | `rule` | 41417.317365 | 701.988430 | 0.348937 | 0.318432 | 1.250136 | 0.966102 |
| `85123A` | `rule` | 53832.751285 | 897.212521 | 0.477703 | 0.427238 | 1.670750 | 0.983333 |

### 17.10 Interpretation of Frozen Summary

The current implementation therefore yields:

- highest total simulated revenue: `ml`
- second-highest total simulated revenue: `rule`
- lowest total simulated revenue: `hybrid`
- lowest mean absolute price change: `hybrid`

This is the central comparative result of the current frozen outputs.

## 18. Statistical Testing Implementation

### 18.1 Module and Output

Statistical testing is implemented in:

- `evaluation/statistical_tests.py`

Output:

- `results/metrics/statistical_tests.json`

### 18.2 Pairing Logic

For each configured comparison, the implementation performs an inner join on:

- `stock_code`
- `invoice_day`

using suffixes for the left and right strategies.

The code raises an error if the aligned dataframe length does not exactly match both original inputs. This ensures that the comparison is truly paired.

### 18.3 Tested Quantities

Two quantities are tested:

- revenue: `predicted_revenue`
- stability: `abs_price_change`

### 18.4 Statistical Tests Applied

For each comparison and each tested quantity, the code applies:

- `scipy.stats.ttest_rel`
- `scipy.stats.wilcoxon`

If every paired difference is numerically zero, the implementation returns a neutral result:

- statistic `0.0`
- p-value `1.0`
- sample size equal to the number of observations

### 18.5 Current Comparison Set

The current configured comparisons are:

- `hybrid_vs_ml`
- `hybrid_vs_rule`

No direct `ml_vs_rule` test is currently written by the implementation.

### 18.6 Statistical Test JSON Structure

The top-level JSON contains:

- `revenue_tests`
- `stability_tests`

Each section contains the configured comparison names, and each comparison contains:

- `paired_ttest`
- `wilcoxon`

Each test result contains:

- `statistic`
- `p_value`
- `sample_size`

### 18.7 Validation Rules for Statistical Tests

`validate_evaluation_tests()` requires:

- exact top-level sections
- exact comparison names
- exact test names
- exact scalar fields in each test payload
- `0 <= p_value <= 1`
- `sample_size > 0`

### 18.8 Current Frozen Statistical Results

Current sample size for every test is:

- `266`

Current revenue tests:

| Comparison | Test | Statistic | P-value |
| --- | --- | ---: | ---: |
| `hybrid_vs_ml` | Paired t-test | -9.11452105497263 | 2.0159424588896765e-17 |
| `hybrid_vs_ml` | Wilcoxon | 0.0 | 2.2259158724964484e-25 |
| `hybrid_vs_rule` | Paired t-test | -4.15141204759827 | 4.4580455217169376e-05 |
| `hybrid_vs_rule` | Wilcoxon | 13568.0 | 0.09819870620532828 |

Current stability tests:

| Comparison | Test | Statistic | P-value |
| --- | --- | ---: | ---: |
| `hybrid_vs_ml` | Paired t-test | -13.456489904499222 | 8.252618360769501e-32 |
| `hybrid_vs_ml` | Wilcoxon | 371.0 | 7.534432739527186e-36 |
| `hybrid_vs_rule` | Paired t-test | -12.701145861437018 | 3.455550362753332e-29 |
| `hybrid_vs_rule` | Wilcoxon | 1243.0 | 1.0559464666416308e-36 |

### 18.9 Statistical Interpretation of the Frozen Results

Under the current artifacts:

- hybrid differs significantly from ML on both revenue and stability under both tests
- hybrid differs significantly from rule on stability under both tests
- hybrid vs rule revenue is significant under the paired t-test but not under Wilcoxon at the 0.05 threshold

This means the revenue difference between hybrid and rule is weaker and more test-sensitive than the hybrid-versus-ML revenue difference.

## 19. Dashboard Implementation

### 19.1 Module

The dashboard is implemented in:

- `dashboard/app.py`

### 19.2 Dashboard Design Principle

The dashboard is strictly read-only. It does not compute metrics, rerun simulations, or modify analysis artifacts.

It only reads:

- `results/metrics/strategy_metrics.parquet`
- `results/metrics/strategy_summary.json`
- `results/metrics/statistical_tests.json`

### 19.3 Startup Behaviour

On startup, the dashboard:

- configures logging for the dashboard target
- sets Streamlit page config
- attempts to load dashboard inputs
- stops with a visible error if required artifacts are missing or invalid

### 19.4 Cached Input Loading

`load_dashboard_inputs()` is decorated with:

- `@st.cache_data(show_spinner=False)`

This caches the dashboard inputs between rerenders.

### 19.5 Input Validation

Before rendering, the dashboard:

- checks that all three required evaluation files exist
- reads the parquet and JSON files
- validates:
  - full evaluation metrics table
  - evaluation summary JSON
  - evaluation statistical tests JSON
- filters product-level rows only after validation

This is an important design choice. The dashboard validates the full artifact contracts before subsetting for presentation.

### 19.6 Product Metrics View Validation

`_dashboard_product_metrics_view()` additionally checks:

- product-level rows are not empty
- the actual strategies present exactly match `{"rule", "ml", "hybrid"}`
- `stock_code` is converted to string
- rows are stably sorted by `(stock_code, strategy)`

### 19.7 Dashboard Sections

The dashboard currently renders:

1. Overall Strategy Performance Comparison
2. Revenue Performance Analysis
3. Pricing Stability Analysis
4. Statistical Significance Tests
5. Supporting Product-Level Comparison

### 19.8 KPI Summary Section

Uses the shared summary metrics, but visually prioritises the dissertation headline metrics:

- primary:
  - `total_revenue`
  - `mean_absolute_change`
- supporting:
  - `mean_daily_revenue`
  - `price_std`
  - `max_price_jump`
  - `change_frequency`

It also computes simple strategy rankings from the already-loaded summary payload to present a concise headline trade-off statement.

The section renders:

- a single consolidated finding sentence naming the revenue leader and stability leader and stating the trade-off between revenue optimisation and price stability
- a bordered strategy-ranking summary box with:
  - `Revenue -> ML`
  - `Stability -> HYBRID`
- a KPI column per strategy containing only the two primary metrics
- a supporting metrics table for the remaining four measures
- visual winner emphasis so the revenue leader and stability leader are easy to identify

### 19.9 Revenue and Stability Charts

Revenue section renders bar charts for:

- `total_revenue`
- `mean_daily_revenue`

The interpretation text explicitly treats `total_revenue` as the main revenue outcome and `mean_daily_revenue` as a secondary contextual measure.

Stability section renders bar charts for:

- `mean_absolute_change`
- `price_std`
- `max_price_jump`
- `change_frequency`

The stability layout gives `mean_absolute_change` full-width emphasis first, followed by three additional full-width supporting charts so the visual layout remains readable on smaller screens.

### 19.10 Product-Level Comparison

The dashboard provides:

- a "Select Product" select box (labelled by product stock code)
- one full-width bar chart per product comparison metric
- a tabular per-strategy comparison for the selected stock code

### 19.11 Statistical Tests Section

The nested JSON statistical results are flattened into a dataframe with columns:

- `Comparison`
- `Metric`
- `Test`
- `Statistic`
- `p-value`
- `Sample Size`
- `Significant`

Significance is defined as:

- `p_value < 0.05`

The rendered dashboard additionally:

- places the statistical section before the supporting product-level section
- states that results are interpreted at `alpha = 0.05`
- lists significant findings explicitly above the full table
- adds a `Conclusion` column with `Significant` or `Not significant`
- highlights the entire row in green for significant results; applies the orange tint only to the `Conclusion` cell for non-significant results

## 20. Exact Frozen Schemas and Contracts

This section consolidates the exact schemas enforced across the project.

### 20.1 Cleaned Transactions

```text
invoice
stock_code
description
quantity
invoice_date
price
customer_id
country
```

### 20.2 Selected Products

```text
stock_code
description
revenue
price_std
active_days
```

### 20.3 Daily Aggregation

```text
stock_code
invoice_day
daily_units
avg_daily_price
daily_revenue
```

### 20.4 Feature Data

```text
stock_code
invoice_day
daily_units
avg_daily_price
daily_revenue
lag1_units
lag7_units
rolling7_mean_units
weekday
month
weekday_0
weekday_1
weekday_2
weekday_3
weekday_4
weekday_5
weekday_6
month_1
month_2
month_3
month_4
month_5
month_6
month_7
month_8
month_9
month_10
month_11
month_12
```

### 20.5 Model Feature Columns

```text
lag1_units
lag7_units
rolling7_mean_units
avg_daily_price
weekday_0
weekday_1
weekday_2
weekday_3
weekday_4
weekday_5
weekday_6
month_1
month_2
month_3
month_4
month_5
month_6
month_7
month_8
month_9
month_10
month_11
month_12
```

### 20.6 Simulation Candidates

```text
invoice_day
stock_code
candidate_price
predicted_demand
predicted_revenue
candidate_rank_by_revenue
```

### 20.7 Simulation Results

```text
invoice_day
stock_code
base_price
previous_price
chosen_price
price_change
abs_price_change
predicted_demand
predicted_revenue
strategy_name
```

### 20.8 Evaluation Metrics

```text
stock_code
strategy
metric_level
total_revenue
mean_daily_revenue
mean_absolute_change
price_std
max_price_jump
change_frequency
```

### 20.9 Evaluation Summary JSON Metric Keys

```text
total_revenue
mean_daily_revenue
mean_absolute_change
price_std
max_price_jump
change_frequency
```

### 20.10 Evaluation Tests JSON Scalar Keys

```text
statistic
p_value
sample_size
```

## 21. Frozen Artifact Inventory

### 21.1 Processed Data Artifacts

- `data/processed/clean_transactions.parquet`
- `data/processed/selected_products.parquet`
- `data/processed/daily_product_data.parquet`
- `data/processed/feature_train_data.parquet`
- `data/processed/feature_test_data.parquet`

### 21.2 Model Artifacts

- `models/artifacts/demand_model.joblib`
- `results/metrics/demand_model_metrics.json`

### 21.3 Simulation Artifacts

- `results/simulation/rule_candidates.parquet`
- `results/simulation/rule_results.parquet`
- `results/simulation/ml_candidates.parquet`
- `results/simulation/ml_results.parquet`
- `results/simulation/hybrid_candidates.parquet`
- `results/simulation/hybrid_results.parquet`

### 21.4 Evaluation Artifacts

- `results/metrics/strategy_metrics.parquet`
- `results/metrics/strategy_summary.json`
- `results/metrics/statistical_tests.json`

### 21.5 Reporting and Audit Artifacts

- `results/reports/raw_inspection_report.json`
- `results/reports/product_selection_report.json`
- `logs/build.log`
- `logs/simulate.log`
- `logs/evaluate.log`
- `logs/dashboard.log`
- `logs/master.log`

## 22. Current Verified Run Status

Based on the current logs and artifacts, the main frozen outputs were generated on `2026-05-03`.

Key visible timestamps include:

- build log entries on `2026-05-03 11:48`
- simulation log entries on `2026-05-03 11:48`
- evaluation log entries on `2026-05-03 11:48`
- dashboard log entries on `2026-05-03 11:49` and `2026-05-03 11:50`

The current artifacts therefore represent a coherent frozen run state from `2026-05-03`.

## 23. Dissertation-Ready Interpretation

The current implementation supports the following evidence-backed narrative:

- The repository implements a staged, reproducible pricing experiment rather than a monolithic script.
- All downstream steps rely on frozen machine-readable artifacts and exact schema validators.
- The data-processing pipeline narrows the raw transactional dataset to a UK-only, five-product analytical universe.
- The demand model is fixed to a single linear regression baseline trained on lag, price, and calendar features.
- All strategy comparisons occur within the same simulator, using the same test rows and the same candidate price sets.
- Under the current frozen outputs, the ML strategy achieves the highest simulated revenue.
- Under the current frozen outputs, the hybrid strategy achieves the lowest average magnitude of price changes and the lowest price dispersion among the three strategies.
- The rule-based strategy sits between ML and hybrid in revenue, while remaining relatively unstable in pricing compared with the hybrid strategy.
- Statistical testing strongly supports hybrid-versus-ML differences and strongly supports hybrid-versus-rule stability differences.

## 24. Important Methodological and Technical Boundaries

The dissertation should also state the implementation boundaries clearly:

- Only one dataset slice is used.
- Only one country is analyzed.
- Only five products are included.
- All pricing outcomes are simulated from predicted demand rather than measured from a live intervention.
- The demand model is weak in predictive terms and should be framed as a fixed comparative baseline rather than a forecasting contribution.
- No multiple-testing correction is implemented in the current statistical testing code.
- No causal demand estimation, counterfactual experimental design, or live A/B deployment is implemented.

## 25. Most Useful Supporting Files for Dissertation Writing

For dissertation drafting, the most useful sources in this repository are:

- `implementation.md`
- `results/reports/raw_inspection_report.json`
- `results/reports/product_selection_report.json`
- `results/metrics/demand_model_metrics.json`
- `results/metrics/strategy_summary.json`
- `results/metrics/statistical_tests.json`

In summary, the current implementation is sufficiently complete and sufficiently instrumented to support a dissertation methods chapter, implementation appendix, and results chapter, provided the forecasting limitations and simulation boundaries are reported transparently.
