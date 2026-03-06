import json
import logging
from pathlib import Path
import sys

import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Ensure project-root imports work when executing this file directly.
PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from config import (
    FEATURE_TEST_DATA_PATH,
    FEATURE_TRAIN_DATA_PATH,
    PHASE6_FEATURE_COLUMNS,
    PHASE6_METRICS_PATH,
    PHASE6_MODEL_ARTIFACT_PATH,
    PHASE6_TARGET_COLUMN,
    PROJECT_ROOT,
)
from preprocessing.common import configured_root, ensure_required_columns
from utils.data_contracts import validate_phase5_features

logger = logging.getLogger(__name__)

CONFIGURED_ROOT_PATH = configured_root(PROJECT_ROOT)
TRAIN_INPUT_PATH = CONFIGURED_ROOT_PATH / FEATURE_TRAIN_DATA_PATH
TEST_INPUT_PATH = CONFIGURED_ROOT_PATH / FEATURE_TEST_DATA_PATH
MODEL_OUTPUT_PATH = CONFIGURED_ROOT_PATH / PHASE6_MODEL_ARTIFACT_PATH
METRICS_OUTPUT_PATH = CONFIGURED_ROOT_PATH / PHASE6_METRICS_PATH


def _validate_phase6_input(df: pd.DataFrame, split_name: str) -> None:
    validate_phase5_features(df, split_name)
    required = PHASE6_FEATURE_COLUMNS + [PHASE6_TARGET_COLUMN]
    ensure_required_columns(df, required, f"Phase 6 {split_name} model input")
    if df[required].isna().any().any():
        raise ValueError(f"Phase 6 {split_name} model input validation failed: null values found.")


def run_phase6() -> None:
    logger.info("Phase 6 demand model training started.")
    logger.info("Input training dataset: %s", TRAIN_INPUT_PATH)
    logger.info("Input testing dataset: %s", TEST_INPUT_PATH)
    logger.info("Output model artifact: %s", MODEL_OUTPUT_PATH)
    logger.info("Output model metrics: %s", METRICS_OUTPUT_PATH)

    if not TRAIN_INPUT_PATH.exists():
        raise FileNotFoundError(f"Phase 6 training dataset not found: {TRAIN_INPUT_PATH}")
    if not TEST_INPUT_PATH.exists():
        raise FileNotFoundError(f"Phase 6 testing dataset not found: {TEST_INPUT_PATH}")

    train_df = pd.read_parquet(TRAIN_INPUT_PATH)
    test_df = pd.read_parquet(TEST_INPUT_PATH)
    _validate_phase6_input(train_df, "train")
    _validate_phase6_input(test_df, "test")

    x_train = train_df[PHASE6_FEATURE_COLUMNS]
    y_train = train_df[PHASE6_TARGET_COLUMN]
    x_test = test_df[PHASE6_FEATURE_COLUMNS]
    y_test = test_df[PHASE6_TARGET_COLUMN]

    model = LinearRegression()
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(mean_squared_error(y_test, y_pred) ** 0.5)
    r2 = float(r2_score(y_test, y_pred))

    metrics = {
        "model_type": "LinearRegression",
        "target": PHASE6_TARGET_COLUMN,
        "features": PHASE6_FEATURE_COLUMNS,
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
    }

    MODEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_OUTPUT_PATH)
    METRICS_OUTPUT_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    logger.info(
        "Phase 6 summary | train rows: %s | test rows: %s | MAE: %.6f | RMSE: %.6f | R2: %.6f",
        len(train_df),
        len(test_df),
        mae,
        rmse,
        r2,
    )
    logger.info("Phase 6 demand model training completed successfully.")


if __name__ == "__main__":
    run_phase6()
