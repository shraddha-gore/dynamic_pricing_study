# Artifact Map

## Purpose

This document maps pipeline commands to their outputs and explains how each output can be used in the dissertation. It is designed as a quick reference while writing methods, results, and appendix sections.

## Command to Artifact Overview

| Command | Main outputs | Dissertation use |
| --- | --- | --- |
| `python main.py --build` | processed data artifacts and model artifacts | Methods chapter, preprocessing description, model setup |
| `python main.py --simulate rule` | rule simulation candidate and result files | Strategy-specific appendix evidence |
| `python main.py --simulate ml` | ML simulation candidate and result files | Strategy-specific appendix evidence |
| `python main.py --simulate hybrid` | hybrid simulation candidate and result files | Strategy-specific appendix evidence |
| `python main.py --simulate all` | all simulation outputs | Full comparative rerun |
| `python main.py --evaluate` | strategy metrics, summary JSON, statistical tests | Results chapter, tables, significance reporting |
| `python main.py --validate` | validation summary JSON | Reproducibility and robustness section |
| `streamlit run dashboard/app.py` | dashboard session and dashboard log | Demonstration only, not primary analytical evidence |

## Build Artifacts

### Raw Input

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `data/raw/online_retail_II_2010_2011.csv` | external source export | Immutable raw dataset | Data source and provenance |

### Inspection

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `results/reports/raw_inspection_report.json` | inspection stage in `--build` | Records raw data quality signals and descriptive profile | Justifying cleaning rules |
| `logs/inspection.log` | inspection stage in `--build` | Execution log | Appendix or troubleshooting record |

### Cleaning

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `data/processed/clean_transactions.parquet` | cleaning stage in `--build` | Canonical cleaned transactional dataset | Data preprocessing evidence |
| `logs/cleaning.log` | cleaning stage in `--build` | Execution log | Appendix or audit trail |

### Product Selection

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `results/reports/product_selection_report.json` | product selection stage in `--build` | Records selection metrics and final chosen products | Justifying product universe |
| `data/processed/selected_products.parquet` | product selection stage in `--build` | Frozen list of study products | Methods chapter and appendix |
| `logs/product_selection.log` | product selection stage in `--build` | Execution log | Audit trail |

### Aggregation

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `data/processed/daily_product_data.parquet` | aggregation stage in `--build` | Daily product-level time series | Methods chapter |
| `logs/aggregation.log` | aggregation stage in `--build` | Execution log | Audit trail |

### Feature Engineering

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `data/processed/feature_train_data.parquet` | feature engineering stage in `--build` | Model training dataset | Methods appendix |
| `data/processed/feature_test_data.parquet` | feature engineering stage in `--build` | Simulation and model evaluation dataset | Methods appendix |
| `logs/feature_engineering.log` | feature engineering stage in `--build` | Execution log | Audit trail |

### Model Training

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `models/artifacts/demand_model.joblib` | model training stage in `--build` | Frozen trained demand model | Reproducibility record |
| `results/metrics/demand_model_metrics.json` | model training stage in `--build` | MAE, RMSE, and R-squared summary | Demand model performance note |
| `logs/model_training.log` | model training stage in `--build` | Execution log | Audit trail |

## Simulation Artifacts

### Candidate Tables

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `results/simulation/rule_candidates.parquet` | `--simulate rule` | Candidate prices and predicted outcomes for rule strategy | Appendix evidence |
| `results/simulation/ml_candidates.parquet` | `--simulate ml` | Candidate prices and predicted outcomes for ML strategy | Appendix evidence |
| `results/simulation/hybrid_candidates.parquet` | `--simulate hybrid` | Candidate prices and predicted outcomes for hybrid strategy | Appendix evidence |

### Chosen-Price Results

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `results/simulation/rule_results.parquet` | `--simulate rule` | Final rule strategy decisions | Source input to evaluation |
| `results/simulation/ml_results.parquet` | `--simulate ml` | Final ML strategy decisions | Source input to evaluation |
| `results/simulation/hybrid_results.parquet` | `--simulate hybrid` | Final hybrid strategy decisions | Source input to evaluation |
| `logs/simulation.log` | simulation commands | Shared execution log | Audit trail |

## Evaluation Artifacts

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `results/metrics/strategy_metrics.parquet` | `python main.py --evaluate` | Unified product-level and strategy-level metrics table | Tables, plots, appendix |
| `results/metrics/strategy_summary.json` | `python main.py --evaluate` | Headline strategy comparison metrics | Main results chapter |
| `results/metrics/statistical_tests.json` | `python main.py --evaluate` | Paired significance test outputs | Statistical findings section |
| `logs/evaluation.log` | `python main.py --evaluate` | Execution log | Audit trail |

## Validation Artifacts

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `results/validation/validation_summary.json` | `python main.py --validate` | Robustness and rerun consistency record | Reproducibility section |
| `logs/validation.log` | `python main.py --validate` | Execution log | Audit trail |

## Dashboard Artifact Usage

| Artifact | Produced by | Purpose | Dissertation use |
| --- | --- | --- | --- |
| `logs/dashboard.log` | dashboard runtime | Dashboard startup and load log | Optional appendix note |

The dashboard reads:

- `results/metrics/strategy_metrics.parquet`
- `results/metrics/strategy_summary.json`
- `results/metrics/statistical_tests.json`

It does not create new analytical outputs and should not be cited as the source of quantitative results.

## Best Sources by Dissertation Section

### Methods Chapter

- `docs/methodology.md`
- `docs/data_provenance.md`
- `results/reports/raw_inspection_report.json`
- `results/reports/product_selection_report.json`

### Results Chapter

- `results/metrics/strategy_summary.json`
- `results/metrics/strategy_metrics.parquet`
- `results/metrics/statistical_tests.json`

### Reproducibility or Appendix

- `docs/reproducibility.md`
- `results/validation/validation_summary.json`
- `logs/*.log`

## Writing Tip

When citing a result in the dissertation, prefer the smallest stable artifact that directly supports the claim:

- use `strategy_summary.json` for headline comparative metrics
- use `statistical_tests.json` for significance claims
- use `validation_summary.json` for reproducibility claims
- use `docs/methodology.md` for process descriptions
