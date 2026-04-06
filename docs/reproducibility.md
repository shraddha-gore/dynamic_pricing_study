# Reproducibility Guide

## Purpose

This document records the practical steps needed to reproduce the implemented pipeline and locate the frozen artifacts used in the study. It is intended to support dissertation writing, appendix material, and future reruns.

## Environment

- Operating context: local repository execution
- Python dependencies: `requirements.txt`
- Expected virtual environment: `venv`
- Main entrypoint: `main.py`

Activate the virtual environment before running commands:

```bash
source venv/bin/activate
```

## Command Set

The pipeline uses explicit commands only. No implicit default mode is allowed.

### Build

Runs the grouped preprocessing and model-building workflow:

```bash
python main.py --build
```

### Simulate One Strategy

```bash
python main.py --simulate rule
python main.py --simulate ml
python main.py --simulate hybrid
```

### Simulate All Strategies

```bash
python main.py --simulate all
```

### Evaluate

```bash
python main.py --evaluate
```

### Validate

```bash
python main.py --validate
```

### Dashboard

The dashboard is separate from the CLI workflow:

```bash
streamlit run dashboard/app.py
```

## Recommended Reproduction Sequence

For a clean end-to-end rerun, use this order:

1. `python main.py --build`
2. `python main.py --simulate all`
3. `python main.py --evaluate`
4. `python main.py --validate`

This sequence rebuilds the processed datasets and frozen model, generates all strategy simulations, computes comparative metrics and statistical tests, and then performs reproducibility checks.

## Frozen Inputs

The pipeline depends on the following stable source and configuration inputs:

- Raw data: `data/raw/online_retail_II_2010_2011.csv`
- Global constants and paths: `config.py`
- Dependency specification: `requirements.txt`
- Data provenance narrative: `docs/data_provenance.md`

## Key Frozen Outputs

### Processed Data

- `data/processed/clean_transactions.parquet`
- `data/processed/selected_products.parquet`
- `data/processed/daily_product_data.parquet`
- `data/processed/feature_train_data.parquet`
- `data/processed/feature_test_data.parquet`

### Model

- `models/artifacts/demand_model.joblib`
- `results/metrics/demand_model_metrics.json`

### Simulation

- `results/simulation/rule_candidates.parquet`
- `results/simulation/rule_results.parquet`
- `results/simulation/ml_candidates.parquet`
- `results/simulation/ml_results.parquet`
- `results/simulation/hybrid_candidates.parquet`
- `results/simulation/hybrid_results.parquet`

### Evaluation

- `results/metrics/strategy_metrics.parquet`
- `results/metrics/strategy_summary.json`
- `results/metrics/statistical_tests.json`

### Validation

- `results/validation/validation_summary.json`

### Logs

- `logs/inspection.log`
- `logs/cleaning.log`
- `logs/product_selection.log`
- `logs/aggregation.log`
- `logs/feature_engineering.log`
- `logs/model_training.log`
- `logs/simulation.log`
- `logs/evaluation.log`
- `logs/dashboard.log`
- `logs/validation.log`

## Verified Status

- Latest completed build run: `python main.py --build` on 2026-04-05
- Latest strategy simulation runs: `rule`, `ml`, and `hybrid` on 2026-04-05
- Latest evaluation re-execution inside validation: 2026-04-05
- Latest validation run: `python main.py --validate` on 2026-04-05
- Latest dashboard artifact-load verification: `dashboard.app.load_dashboard_inputs()` on 2026-04-05

These dates should be updated only when the frozen outputs are intentionally regenerated.

## Reproducibility Controls in the Implementation

The codebase already includes several controls that support reproducibility:

- Centralized paths and constants in `config.py`
- Exact-schema validation for intermediate and final artifacts
- Explicit command dispatch in `main.py`
- Deterministic ordering and tie-breaking in product selection and strategy logic
- Reuse of one frozen demand model across all strategy simulations
- Validation reruns with strict tolerance checks
- Temporary preservation and restoration of managed artifacts during validation

## Validation Logic

The validation workflow does not retrain the model or permanently replace baseline outputs. Instead, it:

- loads the baseline evaluation summary
- reruns all simulations and evaluation steps
- checks that selected rankings remain stable under parameter perturbations
- checks that regenerated metrics remain within tolerance of the baseline
- restores prior simulation and evaluation artifacts after the run

This makes the validation output suitable for dissertation evidence on stability and reproducibility.

## What to Cite in the Dissertation

For dissertation appendices or reproducibility statements, the most useful commands and outputs are:

- `python main.py --build`
- `python main.py --simulate all`
- `python main.py --evaluate`
- `python main.py --validate`
- `results/metrics/strategy_summary.json`
- `results/metrics/statistical_tests.json`
- `results/validation/validation_summary.json`

## Practical Notes

- If outputs are regenerated intentionally, the verified dates in this document should be updated.
- The dashboard is read-only and should not be treated as a computational stage.
- Markdown files under `docs/` are explanatory records and are not consumed by the executable pipeline.
