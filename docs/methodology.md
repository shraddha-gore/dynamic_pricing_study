# Methodology Notes

## Purpose

This document provides a dissertation-oriented description of the study design implemented in this repository. It summarizes the methodological choices, experimental flow, and interpretive boundaries in a form that can be reused in the methods chapter.

## Study Objective

The study compares three dynamic pricing strategies in a retail SME context:

- Rule-based pricing
- Machine learning pricing
- Hybrid pricing

The comparison focuses on two evaluation dimensions:

- Revenue performance
- Pricing stability

The aim is not to compare multiple demand forecasting architectures. Instead, one frozen demand model is used so that observed differences can be attributed to pricing strategy behaviour under a shared simulation environment.

## Dataset and Scope

The study uses the 2010-2011 worksheet from the Online Retail II dataset. Only the exported CSV version stored at `data/raw/online_retail_II_2010_2011.csv` is used as raw input. No 2009 data is included.

The raw CSV is treated as immutable. All analytical transformations begin only after the raw inspection stage. Data provenance is documented separately in `docs/data_provenance.md`.

The analytical scope is deliberately restricted to:

- One market: United Kingdom
- One observation window: the 2010-2011 worksheet period
- Five selected products
- Daily product-level aggregation
- One global linear regression demand model

These constraints were chosen to maintain temporal coherence, reduce cross-market confounding, and keep the pricing comparison focused and interpretable.

## Pipeline Design

The implementation follows this staged workflow:

1. Raw data inspection
2. Transaction cleaning
3. Product selection
4. Daily aggregation
5. Feature engineering
6. Demand model training
7. Strategy simulation
8. Evaluation and statistical testing
9. Dashboard presentation
10. Validation and reproducibility checks

Each stage writes machine-readable artifacts for downstream use. Documentation files are narrative records only and are not consumed by the pipeline.

## Data Inspection

The inspection stage profiles dataset shape, missingness, cancellation patterns, invalid quantities and prices, country distribution, revenue by country, and date coverage. This stage is descriptive only. Its role is to justify later cleaning decisions without altering the raw input.

Frozen inspection findings include:

- 541,910 rows
- 8 columns
- 9,288 cancellations
- 10,624 negative quantities
- 2 negative prices
- 2,515 zero prices

These findings support the later removal of cancelled invoices, negative quantities, and non-positive prices.

## Cleaning Procedure

Cleaning converts the raw headers to a canonical `snake_case` schema and applies deterministic rules designed to preserve retail realism while removing structurally invalid records.

The cleaning logic includes:

- Restricting records to the United Kingdom
- Removing cancelled invoices
- Removing negative quantities
- Removing zero or negative prices
- Excluding non-product administrative or service stock codes
- Reviewing extreme positive prices and retaining only economically plausible values
- Standardizing types and validating post-clean constraints

The cleaning step is intended to remove entries that do not represent forward retail purchase behaviour. The goal is to avoid contaminating the later demand model and pricing simulation with returns, reversals, accounting artefacts, or service charges.

## Product Selection

The product universe is deliberately limited to five items. This is a methodological simplification rather than a defect. It reduces experimental complexity while retaining meaningful price variation and commercial relevance.

Products are selected from the cleaned data using:

- Positive price variation
- At least 150 active days
- Revenue ranking

The final frozen products are:

1. `22423` - REGENCY CAKESTAND 3 TIER
2. `85123A` - WHITE HANGING HEART T-LIGHT HOLDER
3. `47566` - PARTY BUNTING
4. `85099B` - JUMBO BAG RED RETROSPOT
5. `22086` - PAPER CHAIN KIT 50'S CHRISTMAS

## Aggregation Strategy

Transactions are aggregated to one row per `(stock_code, invoice_day)`. The daily aggregation produces:

- `daily_units`
- `avg_daily_price`
- `daily_revenue`

Daily granularity is used because it balances responsiveness and stability. It is fine-grained enough to support dynamic pricing analysis while avoiding excessive invoice-level noise.

## Feature Engineering

Feature engineering creates a frozen, model-ready feature set for demand prediction. The design uses lagged demand, rolling demand, current average daily price, and calendar seasonality features.

Core predictive features:

- `lag1_units`
- `lag7_units`
- `rolling7_mean_units`
- `avg_daily_price`

Seasonality controls:

- Weekday one-hot indicators
- Month one-hot indicators

Rows lacking sufficient lag history are dropped after feature creation. The final data is split chronologically per product with an 80/20 train-test split and no shuffling. This preserves temporal order and prevents future leakage into the training set.

## Demand Model

The study uses a single global linear regression model to predict `daily_units`.

This choice was made for methodological clarity:

- It provides an interpretable baseline
- It avoids turning the dissertation into a model-architecture comparison
- It keeps the pricing strategies under one shared demand surface

The model is trained once on the frozen training dataset and then reused unchanged across all pricing simulations. In this design, the demand model is not itself the main experimental subject. It is a controlled component used to evaluate downstream pricing decisions.

The latest frozen model metrics are:

- MAE: 203.9837
- RMSE: 269.8077
- R-squared: -1.1479

These values should be discussed honestly in the dissertation. The model serves as a fixed forecasting baseline for comparative pricing experiments rather than as a high-performing forecasting contribution.

## Pricing Strategy Definitions

### Rule-Based Strategy

The rule-based strategy is a deterministic heuristic baseline. It compares predicted demand at the base price with the rolling 7-day mean demand and applies a fixed upward or downward adjustment. The final price must still be selected from the simulator's candidate grid.

This strategy represents an intuitive operational baseline that a small retailer could understand and implement without complex optimization logic.

### Machine Learning Strategy

The machine learning strategy selects the candidate price that maximizes predicted revenue. It applies no explicit stability constraint and therefore represents the unconstrained optimization benchmark.

This strategy is included to estimate the highest revenue-seeking behaviour available under the shared demand model and candidate price grid.

### Hybrid Strategy

The hybrid strategy begins from the machine learning optimal price but adds operational stability controls:

- Daily clamp constraint
- Exponential smoothing
- Final projection back to the candidate grid

This strategy is intended to model a more realistic retail decision process in which algorithmic recommendations are moderated by practical pricing governance.

## Shared Simulation Environment

All three strategies are evaluated inside one common simulation engine. For each product-day in the test set:

- The observed `avg_daily_price` becomes the base price
- A fixed candidate price grid is generated within plus or minus 5 percent
- The frozen demand model predicts demand for each candidate
- Predicted revenue is computed for each candidate
- The strategy chooses one final price

This shared simulator is essential to the comparative design because it ensures:

- identical candidate sets across strategies
- identical demand predictions across strategies
- identical test rows across strategies

As a result, strategy differences are driven by decision logic rather than by inconsistent data handling.

## Evaluation Design

Evaluation is performed on the simulation outputs, not on the original transactional data. Revenue is taken directly from simulator predictions, and pricing stability is calculated from simulated price trajectories.

Summary metrics include:

- `total_revenue`
- `mean_daily_revenue`
- `mean_absolute_change`
- `price_std`
- `max_price_jump`
- `change_frequency`

The first two metrics capture economic outcomes. The remaining four metrics capture different aspects of price volatility and operational stability.

## Statistical Testing

Statistical comparison is performed using paired observations aligned on `(stock_code, invoice_day)`. The implemented pairwise comparisons are:

- `hybrid_vs_ml`
- `hybrid_vs_rule`

For each comparison, the pipeline applies:

- Paired t-test
- Wilcoxon signed-rank test

The tested quantities are:

- `predicted_revenue`
- `abs_price_change`

This produces significance evidence for both economic performance and stability outcomes.

## Validation and Reproducibility

The project includes an explicit validation step rather than relying only on conventional unit tests. Validation performs two checks:

- Parameter variation checks for selected hybrid parameters
- Full rerun consistency checks against the frozen baseline summary

The current validation design tests whether:

- `ml` remains highest in total revenue
- `hybrid` remains lowest in mean absolute price change
- regenerated summary metrics remain within a strict tolerance of the baseline

This is useful for dissertation evidence because it directly tests whether the reported comparative conclusions are stable under controlled re-execution.

## Methodological Boundaries

The following boundaries should be stated clearly in the dissertation:

- The study is limited to one dataset slice and one market
- Only five products are analyzed
- The simulation is offline and uses predicted demand rather than live causal response estimation
- The demand model is intentionally fixed and not optimized as a primary research contribution
- The validation stage is lightweight and supports reproducibility claims, not exhaustive software verification

## Recommended Dissertation Use

This document can support the following dissertation sections:

- Research design
- Data and preprocessing
- Experimental methodology
- Pricing strategy definitions
- Evaluation methodology
- Reproducibility statement

This document is intended to stand on its own as a methods-oriented narrative of the study.
