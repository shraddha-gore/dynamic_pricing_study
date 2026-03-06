MASTER IMPLEMENTATION ROADMAP
Dynamic Pricing Comparative Study
Dataset: Online Retail II (2010-2011 Only, CSV Version)

1. PROJECT OVERVIEW
This project implements and comparatively evaluates three pricing strategies within a retail SME context:
- Rule-Based Pricing Strategy
- Machine Learning Pricing Strategy
- Hybrid Pricing Strategy

Evaluation Dimensions:
- Revenue Performance
- Pricing Stability

Layered architecture:
Data -> Inspection -> Cleaning -> Product Selection -> Aggregation -> Feature Engineering -> Demand Model -> Pricing Strategies -> Simulation -> Evaluation -> Dashboard -> Documentation -> Reproducibility

Scope constraints:
- Dataset limited to 2010-2011 only
- No 2009 data
- Comparison focuses on pricing strategies (not multiple demand model architectures)

2. DATA SOURCE
Dataset:
- Online Retail II, 2010-2011 worksheet only

Format:
- Original: Excel (.xlsx)
- Working: CSV

Project location:
- data/raw/online_retail_II_2010_2011.csv

Temporal coverage:
- December 2010 to December 2011 (as present in source)

Data provenance:
- Column names preserved during export
- No row removal during export
- No filtering during export
- No transformations during export
- Raw CSV is immutable input
- Cleaning starts from Phase 2
- Provenance documentation: docs/data_provenance.md

GLOBAL EXECUTION RULES
- Run all phases inside venv: `source venv/bin/activate`
- Define global constants in `config.py`
- No hardcoded paths or column names
- Train demand model once (Phase 6)
- Simulation uses predicted demand only

IMPLEMENTATION BEST PRACTICES (ALL PHASES)
- Machine-readable handoffs first:
  - Any phase consumed by another phase must write a machine-readable artifact (parquet/csv).
  - Markdown/docs are for human reporting only and must not be used as downstream inputs.
- Output data contracts:
  - Each phase must validate required columns, null constraints, and core sanity checks before success.
  - For frozen phase outputs, validate exact schema (column names and order), not only required-column presence.
  - Fail fast on contract violations.
- Schema freezing rule (mandatory for machine-readable handoffs):
  - Any phase that outputs data consumed downstream must define frozen schema constants in `config.py` (pattern: `PHASE{N}_FROZEN_COLUMNS`).
  - Any phase that defines model-input features must additionally freeze the feature list (pattern: `PHASE{N}_FROZEN_FEATURE_COLUMNS`).
  - `utils/data_contracts.py` must enforce exact-column validation before phase completion.
  - Any schema change is a controlled change and must update `config.py`, validators, and `implementation.md` together.
- Single source of truth:
  - All paths, thresholds, feature names, and strategy parameters must be centralized in `config.py`.
  - No hardcoded constants inside phase modules.
- Global schema naming convention:
  - All processed/intermediate dataset columns must use `snake_case`.
  - Raw source headers may retain original naming, but must be normalized to canonical `snake_case` at ingestion (Phase 2).
- Phase-local concise logging:
  - Log only key summaries (row counts, key filters, date ranges, output path).
  - Detailed tables or diagnostics should be `DEBUG` level.
- Deterministic behavior:
  - Use stable sorting before top-k selections.
  - Avoid implicit randomness; if needed, fix seeds explicitly.
  - Preserve chronological processing for time-dependent phases.
- Reproducibility checks:
  - After each phase run, verify output existence and schema validity.
  - Phase reruns should be idempotent for identical inputs/config.
- Documentation sync rule:
  - Any logic or handoff change must update the relevant phase section in `implementation.md`.
  - Keep outputs, frozen results, and executable coverage notes aligned with code.

GLOBAL CONFIGURATION REQUIREMENTS
Centralize in `config.py`:
- Paths: `RAW_DATA_PATH`, `CLEAN_DATA_PATH`, `RESULTS_PATH`
- Raw source columns: `RAW_COL_INVOICE`, `RAW_COL_STOCK_CODE`, `RAW_COL_DESCRIPTION`, `RAW_COL_QUANTITY`, `RAW_COL_PRICE`, `RAW_COL_INVOICE_DATE`, `RAW_COL_CUSTOMER_ID`, `RAW_COL_COUNTRY`
- Canonical columns (snake_case): `COL_INVOICE`, `COL_STOCK_CODE`, `COL_DESCRIPTION`, `COL_QUANTITY`, `COL_PRICE`, `COL_INVOICE_DATE`, `COL_CUSTOMER_ID`, `COL_COUNTRY`
- Raw-to-canonical mapping: `RAW_TO_CANONICAL_COLUMNS`
- Frozen output schemas: `PHASE2_FROZEN_COLUMNS`, `PHASE3_FROZEN_COLUMNS`, `PHASE4_FROZEN_COLUMNS`, `PHASE5_FROZEN_COLUMNS`
- Frozen Phase 5 model feature schema: `PHASE5_FROZEN_FEATURE_COLUMNS`
- Phase 6 model schema params: `PHASE6_FEATURE_COLUMNS`, `PHASE6_TARGET_COLUMN`
- Future phases must follow the same freeze pattern before being marked `Completed`
- Experimental params: `TRAIN_SPLIT_RATIO`, `PRICE_GRID_PERCENTAGE`, `MAX_DAILY_CHANGE`, `HYBRID_SMOOTHING_ALPHA`
- Phase 2 params: `TARGET_COUNTRY`, `INVOICE_CANCELLATION_PREFIX`, `PRICE_OUTLIER_THRESHOLD`, `PRICE_OUTLIER_REVIEW_TOP_N`
- Phase 3 params: `MIN_ACTIVE_DAYS`, `SELECTED_PRODUCT_COUNT`, `MIN_PRICE_STD`
- Phase output files: `PHASE1_REPORT_FILE`, `PHASE1_LOG_FILE`, `PHASE2_LOG_FILE`, `PHASE3_REPORT_FILE`, `PHASE3_LOG_FILE`, `PHASE4_LOG_FILE`, `PHASE5_LOG_FILE`, `PHASE6_LOG_FILE`, `EXPERIMENT_LOG_FILE`
- Phase 4 paths: `DAILY_AGG_DATA_PATH`, `SELECTED_PRODUCTS_PATH`
- Phase 5 paths: `FEATURE_TRAIN_DATA_PATH`, `FEATURE_TEST_DATA_PATH`
- Phase 6 paths: `PHASE6_MODEL_ARTIFACT_PATH`, `PHASE6_METRICS_PATH`

3. PHASE 0 - PROJECT STRUCTURE INITIALISATION
Objective:
- Create baseline project architecture and reproducibility controls.

Rationale:
- A stable directory/module layout and centralized configuration are prerequisites for deterministic phase-by-phase execution.
- Early reproducibility controls reduce rework when later phases are added.

Implementation File:
- N/A (initial scaffolding and structure setup)

Outputs:
- Baseline repository structure
- Initial pipeline and configuration modules

Status:
- Completed

Frozen Results:
- Reproducible project skeleton established for phased execution.

4. PHASE 1 - RAW DATA INSPECTION
Objective:
- Understand dataset quality and distribution before transformation.

Rationale:
- Inspection defines evidence-based cleaning rules and avoids assumptions that could bias downstream demand modeling.
- A frozen inspection report creates an auditable basis for Phase 2 decisions.

Implementation File:
- preprocessing/raw_inspection.py

Outputs:
- docs/raw_data_report.md
- logs/phase1.log

Status:
- Completed

Frozen Results:
- Rows: 541,910
- Columns: 8
- Cancellations: 9,288
- Negative quantities: 10,624
- Negative prices: 2
- Zero prices: 2,515
- ~99% of prices <= GBP 18
- Frozen decisions: UK only, remove cancelled invoices, remove negative quantities, remove zero/negative prices

5. PHASE 2 - DATA CLEANING PIPELINE

Objective:

Produce an analytically valid retail transactional dataset suitable for downstream demand modelling and pricing analysis.

Implementation File:

preprocessing/clean_data.py

Outputs:

data/processed/clean_transactions.parquet

logs/phase2.log

Status:

Completed

Cleaning Principles:

Cleaning must:

Remove structurally invalid entries

Preserve genuine retail pricing variation

Avoid artificial smoothing of volatility

Avoid biasing hybrid strategy performance

Exclude non-retail service or administrative transaction codes

Cleaning Rules:

Normalize Raw Headers to Canonical Schema

Procedure:

Map source CSV headers to canonical snake_case names at Phase 2 entry, then use only canonical names downstream.

Mapping:

`Invoice -> invoice`, `StockCode -> stock_code`, `Description -> description`, `Quantity -> quantity`, `InvoiceDate -> invoice_date`, `Price -> price`, `Customer ID -> customer_id`, `Country -> country`

Rationale:

Creates a single consistent schema across all processed datasets while preserving raw-source immutability.

Restrict to United Kingdom

Condition:

country == TARGET_COUNTRY

Rationale:

Ensures a single-market demand environment consistent with the SME retail context.

Remove Cancelled Invoices

Condition:

invoice begins with INVOICE_CANCELLATION_PREFIX

Rationale:

Cancelled invoices represent transaction reversals rather than forward pricing decisions.

Remove Negative Quantities

Condition:

quantity < 0

Rationale:

Negative quantities represent returns or corrections and do not represent forward demand.

Remove Zero or Negative Prices

Condition:

price ≤ 0

Rationale:

Zero or negative prices represent accounting artefacts or corrections rather than valid retail prices.

Exclude Non-Product Service Codes

Certain `stock_code` values represent service charges, adjustments, or administrative entries rather than retail products.

Examples include postage charges, manual accounting adjustments, or marketplace fees.

Condition:

stock_code not in EXCLUDED_STOCK_CODES

Configured in config.py:

EXCLUDED_STOCK_CODES = [
"DOS",
"DOT",
"POST",
"M",
"AMAZONFEE",
"B"
]

Rationale:

These entries do not represent products customers choose and therefore distort demand modelling and price optimisation experiments.

Removing them ensures the dataset reflects true retail item demand.

Handle Extreme Positive Price Outliers

Instead of automatic percentile trimming:

Procedure:

Compute distribution of positive prices

Inspect top PRICE_OUTLIER_REVIEW_TOP_N highest prices

Remove only economically implausible values

Definition of economically implausible:

Prices clearly inconsistent with normal retail item pricing.

Configured threshold:

PRICE_OUTLIER_THRESHOLD = 1000.0

Rationale:

Inspection of the upper tail showed that extreme prices were dominated by service codes and administrative adjustments rather than retail products.

Rows removed after prior cleaning rules:

0

Standardise and Validate Data Types

Procedure:

Trim whitespace on string columns

Normalize casing for identifiers (`invoice`, `stock_code`)

Collapse repeated internal whitespace in Description

Coerce `quantity` and `price` to numeric and drop non-numeric rows

Coerce `invoice_date` to datetime and drop unparseable rows

Keep `customer_id` as nullable integer (Int64)

Post-clean validation checks:

country must equal TARGET_COUNTRY

quantity must be ≥ 0

price must be > 0 and ≤ PRICE_OUTLIER_THRESHOLD

Required columns must be non-null (except `customer_id`)

Frozen Results:

Country restricted to United Kingdom

Cancelled invoices removed

Negative quantities removed

Non-positive prices removed

Non-product service codes removed

Economically implausible price outliers removed using PRICE_OUTLIER_THRESHOLD

Data type validation checks passed

Output Dataset:

data/processed/clean_transactions.parquet

Phase Handoff Contract:
- Downstream phases may assume cleaned data is UK-only, non-cancelled, non-negative quantity, positive price, and excludes service/admin stock codes.
- Schema is normalized to canonical snake_case column naming.

6. PHASE 3 - PRODUCT SELECTION
Objective:
- Select five stable products for demand modeling and dynamic pricing simulation.

Rationale:
- Restricting to a small set of active, price-varying products controls experiment complexity while preserving meaningful demand-price variation.
- Revenue-ranked selection focuses the study on commercially relevant SKUs.

Implementation File:
- preprocessing/select_products.py

Outputs:
- docs/product_selection.md
- data/processed/selected_products.parquet
- logs/phase3.log

Status:
- Completed

Frozen Results:
- Selection criteria: `price_std > 0`, `active_days >= 150`, ranked by `revenue`
- Products analyzed: 3,801
- Eligible products after filters: 484
- Frozen selected products:
  1. 22423 - REGENCY CAKESTAND 3 TIER
  2. 85123A - WHITE HANGING HEART T-LIGHT HOLDER
  3. 47566 - PARTY BUNTING
  4. 85099B - JUMBO BAG RED RETROSPOT
  5. 22086 - PAPER CHAIN KIT 50'S CHRISTMAS

Phase Handoff Contract:
- Only the frozen five `stock_code` values in `selected_products.parquet` are valid for Phase 4+.
- Product universe must not change unless Phase 3 is intentionally rerun and re-frozen.

7. PHASE 4 - DAILY AGGREGATION
Objective:
- Aggregate transactional data to daily product-level time series for Phase 3 selected products.

Rationale:
- Daily granularity balances responsiveness and stability for pricing simulation.
- Aggregation removes invoice-level noise while preserving demand and price signals required for lag features.

Implementation File:
- preprocessing/aggregate_daily.py

Outputs:
- data/processed/daily_product_data.parquet
- logs/phase4.log

Status:
- Completed

Frozen Results:
- Source data: `data/processed/clean_transactions.parquet`
- Product scope source: `data/processed/selected_products.parquet`
- Aggregation keys: `stock_code`, `invoice_day`
- Computed metrics:
  - `daily_units = sum(quantity)`
  - `avg_daily_price = mean(price)`
  - `daily_revenue = sum(price * quantity)`
- Latest run summary:
  - Input rows: 484,082
  - Filtered rows (selected products): 8,680
  - Aggregated output rows: 1,358
  - Unique products: 5
  - Date range: 2010-12-01 to 2011-12-09

Phase Handoff Contract:
- Phase 5 expects one row per (`stock_code`, `invoice_day`) with `daily_units`, `avg_daily_price`, `daily_revenue`.
- Chronological ordering by `invoice_day` is required for lag feature correctness.

8. PHASE 5 - FEATURE ENGINEERING
Objective:
- Create model-ready demand and seasonality features.

Rationale:
- Lag/rolling features encode short-term demand memory needed for demand forecasting.
- Calendar one-hot features allow the linear model to capture non-linear weekday/month effects without imposing ordinal distance assumptions.
- Per-product chronological split prevents leakage from future observations into training.

Implementation File:
- preprocessing/feature_engineering.py

Outputs:
- data/processed/feature_train_data.parquet
- data/processed/feature_test_data.parquet
- logs/phase5.log

Status:
- Completed

Frozen Results:
- Source data: `data/processed/daily_product_data.parquet`
- Base features:
  - `lag1_units`
  - `lag7_units`
  - `rolling7_mean_units`
  - `avg_daily_price`
- Seasonality features:
  - Raw calendar fields: `weekday`, `month`
  - Weekday one-hot columns: `weekday_0` to `weekday_6`
  - Month one-hot columns: `month_1` to `month_12`
- Frozen feature set:
  - `lag1_units`
  - `lag7_units`
  - `rolling7_mean_units`
  - `avg_daily_price`
  - `weekday_0` to `weekday_6`
  - `month_1` to `month_12`
- Split logic: chronological per product, first 80% train / last 20% test, no shuffling
- Lag handling: rows with missing lag features are dropped after feature creation
- Latest run summary:
  - Input rows: 1,358
  - Modeled rows after lag-drop: 1,323
  - Train rows: 1,057
  - Test rows: 266
  - Products covered: 5

Phase Handoff Contract:
- Phase 6 must train on `feature_train_data.parquet` and evaluate on `feature_test_data.parquet`.
- Feature columns and casing are frozen unless a coordinated migration updates all downstream phases.

9. PHASE 6 - DEMAND MODEL TRAINING
Objective:

Train a single demand model for downstream simulation.

Implementation File:

models/demand_model.py

Outputs:

models/artifacts/demand_model.joblib

results/demand_model_metrics.json

logs/phase6.log

Status:

Completed

Rationale:

A single global demand model isolates strategy effects in later comparisons.

Linear regression provides an interpretable baseline demand-response model appropriate for SME retail analysis.

Planned Scope:

Train a Linear Regression model using Phase 5 training data.

Target: daily_units

Features: lag features, avg_daily_price, and seasonality indicators defined in `PHASE6_FEATURE_COLUMNS`.

Evaluate model performance on the Phase 5 test dataset.

Metrics: MAE, RMSE, R².

Persist the trained model artifact and evaluation metrics.

Train once and reuse the frozen model artifact across all pricing strategy simulations.

Frozen Results:

Model type: Linear Regression

Training dataset: data/processed/feature_train_data.parquet

Evaluation dataset: data/processed/feature_test_data.parquet

Feature inputs strictly follow `PHASE6_FEATURE_COLUMNS`

Target column: `PHASE6_TARGET_COLUMN` (`daily_units`)

Latest run summary:
- Train rows: 1,057
- Test rows: 266
- MAE: 203.9837
- RMSE: 269.8077
- R²: -1.1479

Model artifact stored at models/artifacts/demand_model.joblib

Metrics stored at results/demand_model_metrics.json

Phase Handoff Contract:

Phase 7 and all strategy simulations must load the persisted demand model artifact.

No retraining or feature modification is permitted after Phase 6 completion.

All simulations must rely on this frozen model artifact to generate demand predictions.

10. PHASE 7 - SIMULATION ENGINE
Objective:
- Simulate day-level pricing decisions using predicted demand only.

Implementation File:
- simulation/simulator.py

Outputs:
- Simulation result dataset(s) (paths TBD)

Status:
- Planned

Rationale:
- A common simulator ensures strategies are compared under identical demand predictions and candidate sets.
- Using predicted demand only enforces offline counterfactual consistency.

Planned Scope:
- Per test day generate candidate prices in +/-5% grid
- Predict demand for each candidate
- Compute `predicted_revenue = candidate_price * predicted_demand`
- Strategy chooses final price
- Record simulated outcomes with trace fields (date, product, base price, chosen price, predicted demand, predicted revenue)
- Freeze simulation output schema in config before declaring Phase 7 complete

11. PHASE 8 - RULE-BASED STRATEGY
Objective:
- Implement deterministic heuristic pricing baseline.

Implementation File:
- strategies/rule_based.py

Outputs:
- Rule-based simulation outputs (paths TBD)

Status:
- Planned

Rationale:
- The rule-based policy serves as an operationally intuitive baseline that SMEs can understand and implement quickly.
- Determinism provides a stable comparator for ML and Hybrid strategies.

Planned Scope:
- Increase price 2% if predicted demand > rolling mean
- Decrease price 2% if predicted demand < rolling mean
- Clamp daily change at +/-3%

12. PHASE 9 - MACHINE LEARNING STRATEGY
Objective:
- Implement unconstrained revenue-maximizing price selection.

Implementation File:
- strategies/ml_pricing.py

Outputs:
- ML-strategy simulation outputs (paths TBD)

Status:
- Planned

Rationale:
- This strategy estimates the pure optimization ceiling under the shared demand model.
- No clamp/smoothing is intentional to isolate the tradeoff between revenue pursuit and price volatility.

Planned Scope:
- Select candidate price that maximizes predicted revenue
- No clamp
- No smoothing

13. PHASE 10 - HYBRID STRATEGY
Objective:
- Combine ML optimal pricing with operational stability controls.

Implementation File:
- strategies/hybrid_pricing.py

Outputs:
- Hybrid simulation outputs (paths TBD)

Status:
- Planned

Rationale:
- Hybrid directly targets the business tradeoff: retain most ML revenue gains while controlling operational price instability.
- Clamp/smoothing operationalize change-management constraints common in SMEs.

Planned Scope:
- Start with ML-optimal price
- Apply +/-3% daily clamp
- Optional smoothing

14. PHASE 11 - METRICS AND STATISTICAL TESTING
Objective:
- Quantify revenue and stability performance across strategies.

Implementation File:
- evaluation/metrics.py
- evaluation/statistical_tests.py

Outputs:
- Evaluation metrics tables and statistical test results (paths TBD)

Status:
- Planned

Rationale:
- Descriptive metrics show practical effect size while statistical tests assess whether observed differences are robust.
- Revenue and stability must be evaluated jointly to support strategy recommendations.

Planned Scope:
- Revenue metrics: total, mean daily
- Stability metrics: mean absolute change, std dev, max jump, change frequency
- Statistical comparisons: Hybrid vs ML, Hybrid vs Rule

15. PHASE 12 - DASHBOARD
Objective:
- Provide Streamlit-based visualization of results.

Implementation File:
- dashboard/app.py

Outputs:
- Streamlit dashboard app and supporting visuals (paths TBD)

Status:
- Planned

Rationale:
- The dashboard translates technical outputs into decision-ready comparisons for non-technical stakeholders.
- Keeping it inference-only avoids accidental retraining drift during result review.

Planned Scope:
- Visualization only
- No model training in dashboard runtime
- Compare strategy trajectories and KPI summaries for revenue and stability

16. PHASE 13 - ROBUSTNESS CHECKS
Objective:
- Test sensitivity of conclusions to key control parameters.

Implementation File:
- TBD

Outputs:
- docs/robustness_tests.md

Status:
- Planned

Rationale:
- Robustness testing verifies that conclusions are not artifacts of a single parameter choice.
- Sensitivity analysis improves confidence in final recommendations.

Planned Scope:
- Clamp sensitivity
- Smoothing alpha sensitivity
- Train/test split sensitivity

17. PHASE 14 - DOCUMENTATION FREEZE
Objective:
- Freeze reproducibility-critical project state.

Implementation File:
- TBD

Outputs:
- Frozen parameter, log, version, and technical documentation records

Status:
- Planned

Rationale:
- A frozen documentation snapshot ensures external readers can reproduce results exactly from one coherent record.

Planned Scope:
- Freeze parameters, logs, versions, and technical docs

18. PHASE 15 - FINAL REPRODUCIBILITY CHECK
Objective:
- Verify reproducibility by full environment and pipeline rerun.

Implementation File:
- TBD

Outputs:
- Reproducibility verification report (path TBD)

Status:
- Planned

Rationale:
- Final rerun validation confirms the project is reproducible end-to-end, not only phase-by-phase during development.

Planned Scope:
- Recreate environment
- Re-run full pipeline
- Verify identical outputs

Current Implementation Note:
- As of March 6, 2026, executable workflow coverage is Phases 1-6.
- Latest completed run: `python main.py --workflow full`
- Phases 7-15 remain planned and will be added incrementally.

FINAL FROZEN DESIGN DECISIONS
- Dataset restricted to 2010-2011 only
- CSV working format
- UK-only market scope
- Five selected products
- Daily aggregation level
- Chronological 80/20 split per product
- Single demand model (Linear Regression)
- Simulation uses predicted demand only
- Hybrid strategy includes clamp constraint
- No arbitrary statistical trimming without inspection
- Outlier removal must be economically justified and documented
