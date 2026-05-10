from collections.abc import Mapping

import pandas as pd

from config import (
    COL_COUNTRY,
    COL_PRICE,
    COL_QUANTITY,
    COL_STOCK_CODE,
    EVALUATION_COMPARISONS,
    EVALUATION_METRIC_LEVELS,
    EVALUATION_METRIC_COLUMNS,
    EVALUATION_SUMMARY_SCHEMA,
    EVALUATION_TEST_NAMES,
    EVALUATION_TEST_SECTION_METRICS,
    EVALUATION_TESTS_SCHEMA,
    CLEANING_FROZEN_COLUMNS,
    PRODUCT_SELECTION_FROZEN_COLUMNS,
    DAILY_AGGREGATION_FROZEN_COLUMNS,
    FEATURE_DATA_FROZEN_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    FEATURE_MONTH_COLUMNS,
    FEATURE_WEEKDAY_COLUMNS,
    SIMULATION_STRATEGIES,
    SIMULATION_CANDIDATE_FROZEN_COLUMNS,
    SIMULATION_RESULT_FROZEN_COLUMNS,
    PRICE_OUTLIER_THRESHOLD,
    SELECTED_PRODUCT_COUNT,
    TARGET_COUNTRY,
)
from preprocessing.common import ensure_required_columns


def _validate_exact_columns(df: pd.DataFrame, expected_columns: list[str], context: str) -> None:
    actual_columns = list(df.columns)
    if actual_columns != expected_columns:
        raise ValueError(
            f"{context} validation failed: schema mismatch.\n"
            f"Expected columns: {expected_columns}\n"
            f"Actual columns:   {actual_columns}"
        )


def _validate_exact_keys(payload: Mapping[str, object], expected_keys: list[str], context: str) -> None:
    actual_keys = list(payload.keys())
    missing_keys = [key for key in expected_keys if key not in payload]
    extra_keys = [key for key in actual_keys if key not in expected_keys]
    if missing_keys or extra_keys:
        raise ValueError(
            f"{context} validation failed: key mismatch.\n"
            f"Missing keys: {missing_keys}\n"
            f"Extra keys:   {extra_keys}"
        )


def _validate_scalar_type(value: object, expected_type: type, context: str) -> None:
    # Uses strict identity (type() is) rather than isinstance() to reject bool/int subclasses of float.
    if expected_type is float and type(value) is not float:
        raise ValueError(f"{context} validation failed: expected float, got {type(value).__name__}.")
    if expected_type is int and type(value) is not int:
        raise ValueError(f"{context} validation failed: expected int, got {type(value).__name__}.")
    if expected_type is bool and type(value) is not bool:
        raise ValueError(f"{context} validation failed: expected bool, got {type(value).__name__}.")
    if expected_type is str and type(value) is not str:
        raise ValueError(f"{context} validation failed: expected str, got {type(value).__name__}.")


def _validate_typed_mapping(payload: object, expected_schema: dict[str, type], context: str) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError(f"{context} validation failed: expected mapping, got {type(payload).__name__}.")

    _validate_exact_keys(payload, list(expected_schema.keys()), context)
    for field_name, expected_type in expected_schema.items():
        _validate_scalar_type(payload[field_name], expected_type, f"{context}.{field_name}")


def validate_clean_transactions(df: pd.DataFrame) -> None:
    required = CLEANING_FROZEN_COLUMNS
    ensure_required_columns(df, required, "Cleaned transaction dataset")
    _validate_exact_columns(df, CLEANING_FROZEN_COLUMNS, "Cleaned transaction dataset")

    if df.empty:
        raise ValueError("Cleaned transaction dataset validation failed: dataset is empty.")
    if (df[COL_COUNTRY] != TARGET_COUNTRY).any():
        raise ValueError("Cleaned transaction dataset validation failed: non-target country found.")
    if (df[COL_QUANTITY] < 0).any():
        raise ValueError("Cleaned transaction dataset validation failed: negative quantity found.")
    if (df[COL_PRICE] <= 0).any():
        raise ValueError("Cleaned transaction dataset validation failed: non-positive price found.")
    if (df[COL_PRICE] > PRICE_OUTLIER_THRESHOLD).any():
        raise ValueError("Cleaned transaction dataset validation failed: outlier above threshold found.")


def validate_selected_products(df: pd.DataFrame) -> None:
    required = PRODUCT_SELECTION_FROZEN_COLUMNS
    ensure_required_columns(df, required, "Selected products dataset")
    _validate_exact_columns(df, PRODUCT_SELECTION_FROZEN_COLUMNS, "Selected products dataset")

    if df.empty:
        raise ValueError("Selected products validation failed: dataset is empty.")
    if len(df) != SELECTED_PRODUCT_COUNT:
        raise ValueError(f"Selected products validation failed: expected {SELECTED_PRODUCT_COUNT} rows, got {len(df)}.")
    if df[COL_STOCK_CODE].isna().any() or (df[COL_STOCK_CODE].astype("string").str.strip() == "").any():
        raise ValueError("Selected products validation failed: missing stock code found.")


def validate_daily_aggregation(df: pd.DataFrame) -> None:
    required = DAILY_AGGREGATION_FROZEN_COLUMNS
    ensure_required_columns(df, required, "Daily aggregation dataset")
    _validate_exact_columns(df, DAILY_AGGREGATION_FROZEN_COLUMNS, "Daily aggregation dataset")

    if df.empty:
        raise ValueError("Daily aggregation validation failed: dataset is empty.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Daily aggregation validation failed: null stock code found.")
    if df["invoice_day"].isna().any():
        raise ValueError("Daily aggregation validation failed: null invoice_day found.")


def validate_feature_data(df: pd.DataFrame, split_name: str) -> None:
    required = FEATURE_DATA_FROZEN_COLUMNS

    ensure_required_columns(df, required, f"Feature engineering {split_name} feature dataset")
    _validate_exact_columns(df, FEATURE_DATA_FROZEN_COLUMNS, f"Feature engineering {split_name} feature dataset")

    if df.empty:
        raise ValueError(f"Feature engineering {split_name} feature validation failed: dataset is empty.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError(f"Feature engineering {split_name} feature validation failed: null stock code found.")
    if df["invoice_day"].isna().any():
        raise ValueError(f"Feature engineering {split_name} feature validation failed: null invoice_day found.")
    if df[["daily_units", "lag1_units", "lag7_units", "rolling7_mean_units"]].isna().any().any():
        raise ValueError(
            f"Feature engineering {split_name} feature validation failed: null demand values found."
        )
    if (df[["daily_units", "lag1_units", "lag7_units", "rolling7_mean_units"]] < 0).any().any():
        raise ValueError(
            f"Feature engineering {split_name} feature validation failed: negative demand values found."
        )

    weekday_sum = df[FEATURE_WEEKDAY_COLUMNS].sum(axis=1)
    month_sum = df[FEATURE_MONTH_COLUMNS].sum(axis=1)
    if not (weekday_sum == 1).all():
        raise ValueError(
            f"Feature engineering {split_name} feature validation failed: weekday one-hot encoding invalid."
        )
    if not (month_sum == 1).all():
        raise ValueError(
            f"Feature engineering {split_name} feature validation failed: month one-hot encoding invalid."
        )

    missing_frozen_features = [col for col in MODEL_FEATURE_COLUMNS if col not in df.columns]
    if missing_frozen_features:
        raise ValueError(
            f"Feature engineering {split_name} feature validation failed: missing frozen feature columns: {missing_frozen_features}"
        )


def validate_simulation_candidates(df: pd.DataFrame) -> None:
    ensure_required_columns(df, SIMULATION_CANDIDATE_FROZEN_COLUMNS, "Simulation candidate dataset")
    _validate_exact_columns(df, SIMULATION_CANDIDATE_FROZEN_COLUMNS, "Simulation candidate dataset")

    if df.empty:
        raise ValueError("Simulation candidate validation failed: dataset is empty.")
    if df["invoice_day"].isna().any():
        raise ValueError("Simulation candidate validation failed: null invoice_day found.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Simulation candidate validation failed: null stock_code found.")
    if (df["candidate_price"] <= 0).any():
        raise ValueError("Simulation candidate validation failed: non-positive candidate price found.")
    if (df["predicted_demand"] < 0).any():
        raise ValueError("Simulation candidate validation failed: negative predicted demand found.")
    if (df["predicted_revenue"] < 0).any():
        raise ValueError("Simulation candidate validation failed: negative predicted revenue found.")
    if (df["candidate_rank_by_revenue"] < 1).any():
        raise ValueError("Simulation candidate validation failed: invalid candidate rank found.")


def validate_simulation_results(df: pd.DataFrame) -> None:
    ensure_required_columns(df, SIMULATION_RESULT_FROZEN_COLUMNS, "Simulation outcome dataset")
    _validate_exact_columns(df, SIMULATION_RESULT_FROZEN_COLUMNS, "Simulation outcome dataset")

    if df.empty:
        raise ValueError("Simulation outcome validation failed: dataset is empty.")
    if df["invoice_day"].isna().any():
        raise ValueError("Simulation outcome validation failed: null invoice_day found.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Simulation outcome validation failed: null stock_code found.")
    if (df["base_price"] <= 0).any():
        raise ValueError("Simulation outcome validation failed: non-positive base price found.")
    if (df["chosen_price"] <= 0).any():
        raise ValueError("Simulation outcome validation failed: non-positive chosen price found.")
    if (df["previous_price"] <= 0).any():
        raise ValueError("Simulation outcome validation failed: non-positive previous price found.")
    if not ((df["chosen_price"] - df["previous_price"]).round(12) == df["price_change"].round(12)).all():
        raise ValueError(
            "Simulation outcome validation failed: price_change does not match chosen_price - previous_price."
        )
    if not ((df["price_change"].abs()).round(12) == df["abs_price_change"].round(12)).all():
        raise ValueError("Simulation outcome validation failed: abs_price_change mismatch found.")
    if (df["abs_price_change"] < 0).any():
        raise ValueError("Simulation outcome validation failed: negative abs_price_change found.")
    if (df["predicted_demand"] < 0).any():
        raise ValueError("Simulation outcome validation failed: negative predicted demand found.")
    if (df["predicted_revenue"] < 0).any():
        raise ValueError("Simulation outcome validation failed: negative predicted revenue found.")


def validate_evaluation_metrics(df: pd.DataFrame) -> None:
    ensure_required_columns(df, EVALUATION_METRIC_COLUMNS, "Evaluation strategy metrics dataset")
    _validate_exact_columns(df, EVALUATION_METRIC_COLUMNS, "Evaluation strategy metrics dataset")

    if df.empty:
        raise ValueError("Evaluation strategy metrics validation failed: dataset is empty.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Evaluation strategy metrics validation failed: null stock_code found.")
    if df["strategy"].isna().any() or (df["strategy"].astype("string").str.strip() == "").any():
        raise ValueError("Evaluation strategy metrics validation failed: missing strategy found.")

    expected_strategies = set(SIMULATION_STRATEGIES)
    actual_strategies = set(df["strategy"].astype(str).unique().tolist())
    if actual_strategies != expected_strategies:
        raise ValueError(
            "Evaluation strategy metrics validation failed: strategy mismatch.\n"
            f"Expected strategies: {sorted(expected_strategies)}\n"
            f"Actual strategies:   {sorted(actual_strategies)}"
        )

    actual_metric_levels = set(df["metric_level"].astype(str).unique().tolist())
    expected_metric_levels = set(EVALUATION_METRIC_LEVELS)
    if actual_metric_levels != expected_metric_levels:
        raise ValueError(
            "Evaluation strategy metrics validation failed: metric_level mismatch.\n"
            f"Expected levels: {sorted(expected_metric_levels)}\n"
            f"Actual levels:   {sorted(actual_metric_levels)}"
        )

    metric_columns = list(EVALUATION_SUMMARY_SCHEMA.keys())
    if df[metric_columns].isna().any().any():
        raise ValueError("Evaluation strategy metrics validation failed: null summary metric value found.")


def validate_evaluation_summary(summary_payload: object) -> None:
    if not isinstance(summary_payload, Mapping):
        raise ValueError(
            f"Evaluation strategy summary validation failed: expected mapping, got {type(summary_payload).__name__}."
        )
    if not summary_payload:
        raise ValueError("Evaluation strategy summary validation failed: payload is empty.")

    _validate_exact_keys(summary_payload, list(SIMULATION_STRATEGIES), "Evaluation strategy summary")
    for strategy_name in SIMULATION_STRATEGIES:
        _validate_typed_mapping(
            summary_payload[strategy_name],
            EVALUATION_SUMMARY_SCHEMA,
            f"Evaluation strategy summary[{strategy_name}]",
        )


def validate_evaluation_tests(statistical_payload: object) -> None:
    if not isinstance(statistical_payload, Mapping):
        raise ValueError(
            "Evaluation statistical tests validation failed: "
            f"expected mapping, got {type(statistical_payload).__name__}."
        )
    if not statistical_payload:
        raise ValueError("Evaluation statistical tests validation failed: payload is empty.")

    _validate_exact_keys(
        statistical_payload,
        list(EVALUATION_TEST_SECTION_METRICS.keys()),
        "Evaluation statistical tests",
    )

    expected_comparisons = list(EVALUATION_COMPARISONS.keys())
    expected_tests = list(EVALUATION_TEST_NAMES)
    for section_name in EVALUATION_TEST_SECTION_METRICS:
        comparisons = statistical_payload[section_name]
        if not isinstance(comparisons, Mapping):
            raise ValueError(
                "Evaluation statistical tests validation failed: "
                f"section '{section_name}' must be a mapping."
            )
        _validate_exact_keys(
            comparisons,
            expected_comparisons,
            f"Evaluation statistical tests[{section_name}]",
        )

        for comparison_name in expected_comparisons:
            tests = comparisons[comparison_name]
            if not isinstance(tests, Mapping):
                raise ValueError(
                    "Evaluation statistical tests validation failed: "
                    f"comparison '{comparison_name}' in section '{section_name}' must be a mapping."
                )
            _validate_exact_keys(
                tests,
                expected_tests,
                f"Evaluation statistical tests[{section_name}][{comparison_name}]",
            )

            for test_name in expected_tests:
                test_values = tests[test_name]
                _validate_typed_mapping(
                    test_values,
                    EVALUATION_TESTS_SCHEMA,
                    f"Evaluation statistical tests[{section_name}][{comparison_name}][{test_name}]",
                )

                p_value = test_values["p_value"]
                sample_size = test_values["sample_size"]
                if not 0.0 <= p_value <= 1.0:
                    raise ValueError(
                        "Evaluation statistical tests validation failed: "
                        f"p_value out of range in section '{section_name}', comparison '{comparison_name}', "
                        f"test '{test_name}'."
                    )
                if sample_size <= 0:
                    raise ValueError(
                        "Evaluation statistical tests validation failed: "
                        f"non-positive sample_size in section '{section_name}', comparison '{comparison_name}', "
                        f"test '{test_name}'."
                    )
