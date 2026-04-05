import json
import logging
from pathlib import Path
import sys

import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Ensure project-root imports work when executing this file directly.
if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import (
    FEATURE_TEST_DATA_PATH,
    FEATURE_TRAIN_DATA_PATH,
    MODEL_FEATURE_COLUMNS,
    MODEL_METRICS_PATH,
    MODEL_TYPE,
    MODEL_ARTIFACT_PATH,
    MODEL_TARGET_COLUMN,
    PROJECT_ROOT,
)
from preprocessing.common import configured_path, ensure_required_columns
from utils.data_contracts import validate_feature_data

logger = logging.getLogger(__name__)


def _train_input_path() -> Path:
    return configured_path(PROJECT_ROOT, FEATURE_TRAIN_DATA_PATH)


def _test_input_path() -> Path:
    return configured_path(PROJECT_ROOT, FEATURE_TEST_DATA_PATH)


def _model_output_path() -> Path:
    return configured_path(PROJECT_ROOT, MODEL_ARTIFACT_PATH)


def _metrics_output_path() -> Path:
    return configured_path(PROJECT_ROOT, MODEL_METRICS_PATH)


def _validate_model_input(df: pd.DataFrame, split_name: str) -> None:
    validate_feature_data(df, split_name)
    required = MODEL_FEATURE_COLUMNS + [MODEL_TARGET_COLUMN]
    ensure_required_columns(df, required, f"Model training {split_name} model input")
    if df[required].isna().any().any():
        raise ValueError(f"Model training {split_name} model input validation failed: null values found.")


def run_demand_model_training() -> None:
    train_input_path = _train_input_path()
    test_input_path = _test_input_path()
    model_output_path = _model_output_path()
    metrics_output_path = _metrics_output_path()
    logger.info("Model training started.")
    logger.info("Input training dataset: %s", train_input_path)
    logger.info("Input testing dataset: %s", test_input_path)
    logger.info("Output model artifact: %s", model_output_path)
    logger.info("Output model metrics: %s", metrics_output_path)

    if not train_input_path.exists():
        raise FileNotFoundError(f"Model training dataset not found: {train_input_path}")
    if not test_input_path.exists():
        raise FileNotFoundError(f"Model test dataset not found: {test_input_path}")

    train_df = pd.read_parquet(train_input_path)
    test_df = pd.read_parquet(test_input_path)
    _validate_model_input(train_df, "train")
    _validate_model_input(test_df, "test")

    x_train = train_df[MODEL_FEATURE_COLUMNS]
    y_train = train_df[MODEL_TARGET_COLUMN]
    x_test = test_df[MODEL_FEATURE_COLUMNS]
    y_test = test_df[MODEL_TARGET_COLUMN]

    model = LinearRegression()
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(mean_squared_error(y_test, y_pred) ** 0.5)
    r2 = float(r2_score(y_test, y_pred))

    metrics = {
        "model_type": MODEL_TYPE,
        "target": MODEL_TARGET_COLUMN,
        "features": MODEL_FEATURE_COLUMNS,
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
    }

    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_output_path)
    metrics_output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    logger.info(
        "Model training summary | train rows: %s | test rows: %s | MAE: %.6f | RMSE: %.6f | R2: %.6f",
        len(train_df),
        len(test_df),
        mae,
        rmse,
        r2,
    )
    logger.info("Model training completed successfully.")


if __name__ == "__main__":
    run_demand_model_training()
