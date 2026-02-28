MASTER IMPLEMENTATION ROADMAP

Dynamic Pricing Comparative Study
 Dataset: Online Retail II (2010–2011 Only, CSV Version)

1. PROJECT OVERVIEW
This project implements and comparatively evaluates:
Rule-Based Pricing Strategy


Machine Learning Pricing Strategy


Hybrid Pricing Strategy


Evaluation Dimensions:
Revenue Performance


Pricing Stability


The system follows a layered research architecture:
Data → Inspection → Cleaning → Feature Engineering → Demand Model → Pricing Strategies → Simulation → Evaluation → Dashboard → Documentation → Reproducibility
Scope is strictly limited to the 2010–2011 dataset.
No 2009 data is used anywhere in the pipeline.

2. DATA SOURCE
Dataset:
 Online Retail II – 2010–2011 sheet only
Format:
 CSV
Location:
 data/raw/online_retail_II_2010_2011.csv
Temporal Coverage (as provided in sheet):
 January 2010 – December 2011
No additional sheet merging.
No external data sources.

MANDATORY EXECUTION ENVIRONMENT (ALL PHASES)
All commands and scripts for every phase must run inside the project virtual environment.
Activation command:
 source venv/bin/activate

GLOBAL CONFIGURATION RULE (ALL PHASES)
All global constants must be centralised in config.py.
This includes paths, file names, shared schema/column names, and experimental parameters.
Implementation modules must import these constants from config.py instead of redefining them locally.

CURRENT EXECUTION MODEL
Primary entrypoint:
 main.py
Default run (demo / end-to-end available phases):
 python main.py
Single-phase run (development / debugging):
 python main.py --phase 1
Workflow orchestration:
 pipeline/runner.py
Central logging configuration:
 utils/logging_config.py

3. PHASE 0 — PROJECT STRUCTURE INITIALISATION (Completed)
Objective
 Establish experimental architecture and reproducibility controls.
Structure
dynamic_pricing_study/
data/
 raw/
 processed/
preprocessing/
 raw_inspection.py
 clean_data.py
 feature_engineering.py
models/
 demand_model.py
strategies/
 rule_based.py
 ml_pricing.py
 hybrid_pricing.py
simulation/
 simulator.py
evaluation/
 metrics.py
 statistical_tests.py
results/
dashboard/
 app.py
docs/
 data_provenance.md
 raw_data_report.md
logs/
 experiment.log
 phase1.log
pipeline/
 __init__.py
 runner.py
utils/
 __init__.py
 logging_config.py
config.py
 main.py
 requirements.txt
Controls implemented:
Virtual environment created


Dependencies frozen


Logging configured


Constants centralised in config.py (paths and non-path global constants)


Workflow runner and CLI entrypoint wired (main.py + pipeline/runner.py)


Dedicated logging configuration module created (utils/logging_config.py)


Dissertation Link
 Chapter 3 – System Architecture
Status: Complete

4. PHASE 1 — RAW DATA INSPECTION
Objective
 Understand dataset structure before transformation.
Strict Rule
 No filtering, cleaning, or modification in this phase.
Tasks
Load CSV using pandas.read_csv()


Record dataset shape


Inspect column names and data types


Compute null counts and percentages


Identify cancellation invoices (Invoice starting with C)


Analyse quantity distribution


Analyse price distribution


Compute country distribution


Compute revenue per country


Validate date range


Outputs
docs/raw_data_report.md
 logs/phase1.log
 logs/experiment.log
Status
 Complete
Frozen Decisions After Inspection
Keep UK only


Remove cancelled invoices


Remove negative quantities


Remove zero or negative prices


Temporal boundary already fixed at source (2010–2011 only).
Dissertation Link
 Dataset description
 Data justification

IMPLEMENTATION STATUS SNAPSHOT
Implemented in code:
 Phase 1 (raw inspection), orchestration, and logging architecture.
Present as placeholders (files exist but logic pending implementation):
 Phases 2 to 15 modules.

5. PHASE 2 — DATA CLEANING PIPELINE
Objective
 Produce clean transactional dataset under frozen rules.
Cleaning Rules
Keep UK only


Remove cancelled invoices


Remove negative quantities


Remove zero or negative prices


Remove top 1 percent outliers by price


No temporal filtering required.
Output
data/processed/clean_transactions.parquet
File
preprocessing/clean_data.py
Dissertation Link
 Data preparation methodology
 Cleaning assumptions

6. PHASE 3 — PRODUCT SELECTION
Objective
 Select stable products for controlled experimentation.
Steps
Aggregate total revenue per product


Calculate price variance per product


Measure transaction frequency


Ensure product exists consistently across 2010–2011


Selection Criteria
High revenue


Sufficient price variation


Stable availability


Freeze
Top 5 products selected and recorded in docs/product_selection.md
Output
data/processed/selected_products.parquet
Dissertation Link
 Experimental scope control

7. PHASE 4 — DAILY AGGREGATION
Objective
 Convert transactional data to daily product-level demand.
For each product per day compute:
DailyUnits = sum(quantity)


AvgDailyPrice = mean(price)


DailyRevenue


Output
data/processed/daily_product_data.parquet
File
preprocessing/feature_engineering.py

8. PHASE 5 — FEATURE ENGINEERING
Objective
 Prepare dataset for demand modelling.
Features Added
Lag 1 demand


Lag 7 demand


Rolling 7-day average demand


Weekday indicator


Month indicator


Chronological Split
80 percent train


20 percent test


No shuffling.
Freeze
No retraining during simulation.
Outputs
train_data.parquet
 test_data.parquet

9. PHASE 6 — DEMAND MODEL TRAINING
Objective
 Train structural demand prediction model.
Model
Linear Regression
Target
DailyUnits
Features
Lag features
 Price
 Seasonality indicators
Evaluation Metrics
MAE
 RMSE
 R²
Freeze
Single demand model.
 No model comparison.
Output
models/demand_model.pkl
Dissertation Alignment
Matches proposal scope and hypothesis structure.

10. PHASE 7 — SIMULATION ENGINE
Objective
 Create controlled experimental pricing loop.
For each product:
Initial price = last observed training price.
For each test day:
Generate candidate prices (±5 percent grid)


Predict demand using trained model


Compute predicted revenue


Pass candidate prices to pricing strategy


Record selected price, predicted demand, revenue


Critical Rule
Simulation must use predicted demand only.
 Never use real test demand for decision-making.
File
simulation/simulator.py

11. PHASE 8 — RULE-BASED STRATEGY
File
strategies/rule_based.py
Logic
If predicted demand > rolling mean → increase price 2 percent
 If predicted demand < rolling mean → decrease price 2 percent
 Clamp daily change at ±3 percent
Output
results_rule.parquet

12. PHASE 9 — MACHINE LEARNING STRATEGY
File
strategies/ml_pricing.py
Logic
Select candidate price that maximises predicted revenue.
 No smoothing.
 No clamp.
Output
results_ml.parquet

13. PHASE 10 — HYBRID STRATEGY
File
strategies/hybrid_pricing.py
Logic
ML optimal price


Apply clamp ±3 percent


Optional exponential smoothing


Output
results_hybrid.parquet

14. PHASE 11 — METRICS & STATISTICAL TESTING
Files
evaluation/metrics.py
 evaluation/statistical_tests.py
Metrics
Revenue
Total revenue


Mean daily revenue


Stability
Mean absolute price change


Standard deviation of price change


Maximum price jump


Change frequency


Aggregation
Revenue-weighted averages
Statistical Testing
Paired t-tests:
Hybrid vs ML
 Hybrid vs Rule
Output
metrics_summary.parquet
Dissertation Link
Hypothesis testing
 H₀ vs H₁ evaluation

15. PHASE 12 — DASHBOARD
Tool
Streamlit
Reads precomputed results only.
Tabs
Price comparison


Revenue comparison


Stability metrics


Product selector


Strategy selector


No model training inside dashboard.

16. PHASE 13 — ROBUSTNESS CHECKS
Test sensitivity to:
Clamp at 2 percent


Clamp at 5 percent


Different smoothing alpha


Alternative train/test split within 2010–2011


Record in:
docs/robustness_tests.md

17. PHASE 14 — DOCUMENTATION FREEZE
Create
Technical specification


Parameter freeze record


Experiment log


Version record


Ensure reproducibility.

18. PHASE 15 — FINAL REPRODUCIBILITY CHECK
Create fresh environment


Reinstall dependencies


Re-run entire pipeline


Verify identical outputs


Confirms experimental integrity.

FINAL FROZEN DESIGN DECISIONS
Dataset restricted to 2010–2011 only


CSV format


UK only


Five products


Daily aggregation


Chronological split


Single demand model (Linear Regression)


Simulation uses predicted demand only


Hybrid includes clamp constraint


Revenue-weighted aggregation
