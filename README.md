# Dynamic Pricing Study

**MSc Computer Science Dissertation — University of Essex Online**

*A Comparative Study of Rule-Based, Machine Learning and Hybrid Dynamic Pricing Models for Stable and Customer-Centric Pricing in Retail SMEs*

---

## Overview

This repository implements an offline comparative study of three dynamic pricing strategies in a retail SME context:

- **Rule-based pricing** — adjusts price up or down from a base price using a fixed percentage rule driven by predicted demand relative to a rolling baseline
- **Machine learning pricing** — selects the revenue-maximising price from a candidate grid using a trained linear demand model, with no inter-day stability constraint
- **Hybrid pricing** — applies ML-optimal price selection but constrains daily price movement and smooths toward the previous price, trading some revenue for stability

The study is scoped to a single market (United Kingdom), five products, and one shared linear regression demand model. All comparisons occur within the same simulation environment using identical test rows and identical candidate price grids, so strategy differences reflect pricing logic rather than modelling or data differences.

---

## Dissertation Context

| | |
|---|---|
| **Institution** | University of Essex Online |
| **Programme** | MSc Computer Science |
| **Study type** | Offline comparative simulation |
| **Dataset** | [Online Retail II](https://www.kaggle.com/datasets/kabilan45/online-retail-ii-dataset) (2010–2011 worksheet) |
| **Products** | 5 selected UK retail products |
| **Demand model** | Single frozen `LinearRegression` baseline |
| **Outcome dimensions** | Revenue performance and pricing stability |

---

## Repository Structure

```
dynamic_pricing_study/
├── main.py                  # CLI entrypoint
├── config.py                # All shared paths, constants, and parameters
├── pipeline/                # Orchestration and execution naming
├── preprocessing/           # Inspection, cleaning, selection, aggregation, features
├── models/                  # Demand model training
├── strategies/              # Rule-based, ML, and hybrid price selection
├── simulation/              # Shared simulation engine
├── evaluation/              # Metric computation and statistical tests
├── dashboard/               # Streamlit read-only results dashboard
├── utils/                   # Logging, data contracts, artifact loading
├── data/
│   ├── raw/                 # Immutable source CSV
│   └── processed/           # Generated parquet artifacts
├── models/artifacts/        # Serialised demand model
├── results/
│   ├── simulation/          # Per-strategy candidate and result parquets
│   ├── metrics/             # Evaluation metrics, summary, and statistical tests
│   └── reports/             # Inspection and product selection reports
└── logs/                    # Stage-specific and master log files
```

---

## Setup

**Requirements:** Python 3 with the pinned dependencies in `requirements.txt`.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Place the raw source file at:

```
data/raw/online_retail_II_2010_2011.csv
```

This file is the 2010–2011 worksheet of the Online Retail II dataset exported to CSV with original column names preserved and no rows removed.

---

## Commands

### End-to-end pipeline

```bash
python main.py --run-pipeline
```

### Step by step

```bash
python main.py --build       # data preparation and model training
python main.py --simulate    # run all three pricing strategies
python main.py --evaluate    # compute metrics and statistical tests
```

### Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard is read-only and loads pre-computed evaluation artifacts. It renders five sections: overall strategy comparison, revenue analysis, pricing stability analysis, statistical significance tests, and product-level detail.

---

## Pipeline Stages

| Stage | What it does |
|---|---|
| `--build` | Inspects the raw CSV, cleans transactions, selects five products, aggregates to daily product level, engineers lag and calendar features, and trains the demand model |
| `--simulate` | Loads the test features and frozen model, generates a five-point candidate price grid per row, and runs each strategy to produce chosen-price result tables |
| `--evaluate` | Computes product-level and strategy-level metrics, runs paired t-tests and Wilcoxon signed-rank tests for hybrid-vs-ML and hybrid-vs-rule comparisons |

The dashboard does not rerun any computation — it reads the artifacts produced by `--evaluate`.

---

## Key Parameters

| Parameter | Value |
|---|---|
| Train/test split | 80 / 20 (chronological, per product) |
| Candidate price grid | 5 points from −5% to +5% of base price |
| Rule price adjustment | ±2% |
| Hybrid max daily change | ±3% |
| Hybrid smoothing alpha | 0.3 |
| Statistical significance threshold | 0.05 |

---

## Selected Products

| Stock code | Description | Active days |
|---|---|---:|
| 22423 | REGENCY CAKESTAND 3 TIER | 301 |
| 85123A | WHITE HANGING HEART T-LIGHT HOLDER | 305 |
| 47566 | PARTY BUNTING | 291 |
| 85099B | JUMBO BAG RED RETROSPOT | 300 |
| 22086 | PAPER CHAIN KIT 50'S CHRISTMAS | 161 |

Products were selected by ranking eligible UK products (≥150 active days, non-zero price standard deviation) by total revenue and taking the top five.

---

## Methodological Boundaries

- One dataset slice, one country, five products
- All pricing outcomes are simulated from predicted demand — no live intervention
- The demand model is a fixed linear regression baseline used as a comparative anchor, not a forecasting contribution
- No multiple-testing correction applied
- No causal demand estimation or A/B deployment
