from collections.abc import Mapping

import pandas as pd

from config import (
    COL_COUNTRY,
    COL_PRICE,
    COL_QUANTITY,
    COL_STOCK_CODE,
    PHASE11_COMPARISONS,
    PHASE11_METRIC_LEVELS,
    PHASE11_METRIC_COLUMNS,
    PHASE11_SUMMARY_SCHEMA,
    PHASE11_TEST_NAMES,
    PHASE11_TEST_SECTION_METRICS,
    PHASE11_TESTS_SCHEMA,
    PHASE13_PARAMETER_VARIATIONS,
    PHASE13_RANKING_CHECKS,
    PHASE13_RERUN_METRICS,
    PHASE13_RERUN_TOLERANCE,
    PHASE2_FROZEN_COLUMNS,
    PHASE3_FROZEN_COLUMNS,
    PHASE4_FROZEN_COLUMNS,
    PHASE5_FROZEN_COLUMNS,
    PHASE5_FROZEN_FEATURE_COLUMNS,
    PHASE5_MONTH_COLUMNS,
    PHASE5_WEEKDAY_COLUMNS,
    PHASE7_STRATEGIES,
    PHASE7_CANDIDATE_FROZEN_COLUMNS,
    PHASE7_RESULT_FROZEN_COLUMNS,
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
    required = PHASE2_FROZEN_COLUMNS
    ensure_required_columns(df, required, "Phase 2 cleaned dataset")
    _validate_exact_columns(df, PHASE2_FROZEN_COLUMNS, "Phase 2 cleaned dataset")

    if df.empty:
        raise ValueError("Phase 2 cleaned dataset validation failed: dataset is empty.")
    if (df[COL_COUNTRY] != TARGET_COUNTRY).any():
        raise ValueError("Phase 2 cleaned dataset validation failed: non-target country found.")
    if (df[COL_QUANTITY] < 0).any():
        raise ValueError("Phase 2 cleaned dataset validation failed: negative quantity found.")
    if (df[COL_PRICE] <= 0).any():
        raise ValueError("Phase 2 cleaned dataset validation failed: non-positive price found.")
    if (df[COL_PRICE] > PRICE_OUTLIER_THRESHOLD).any():
        raise ValueError("Phase 2 cleaned dataset validation failed: outlier above threshold found.")


def validate_selected_products(df: pd.DataFrame) -> None:
    required = PHASE3_FROZEN_COLUMNS
    ensure_required_columns(df, required, "Phase 3 selected products dataset")
    _validate_exact_columns(df, PHASE3_FROZEN_COLUMNS, "Phase 3 selected products dataset")

    if df.empty:
        raise ValueError("Phase 3 selected products validation failed: dataset is empty.")
    if len(df) != SELECTED_PRODUCT_COUNT:
        raise ValueError(
            f"Phase 3 selected products validation failed: expected {SELECTED_PRODUCT_COUNT} rows, got {len(df)}."
        )
    if df[COL_STOCK_CODE].isna().any() or (df[COL_STOCK_CODE].astype("string").str.strip() == "").any():
        raise ValueError("Phase 3 selected products validation failed: missing stock code found.")


def validate_daily_aggregation(df: pd.DataFrame) -> None:
    required = PHASE4_FROZEN_COLUMNS
    ensure_required_columns(df, required, "Phase 4 daily aggregation dataset")
    _validate_exact_columns(df, PHASE4_FROZEN_COLUMNS, "Phase 4 daily aggregation dataset")

    if df.empty:
        raise ValueError("Phase 4 daily aggregation validation failed: dataset is empty.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Phase 4 daily aggregation validation failed: null stock code found.")
    if df["invoice_day"].isna().any():
        raise ValueError("Phase 4 daily aggregation validation failed: null invoice_day found.")


def validate_phase5_features(df: pd.DataFrame, split_name: str) -> None:
    required = PHASE5_FROZEN_COLUMNS

    ensure_required_columns(df, required, f"Phase 5 {split_name} feature dataset")
    _validate_exact_columns(df, PHASE5_FROZEN_COLUMNS, f"Phase 5 {split_name} feature dataset")

    if df.empty:
        raise ValueError(f"Phase 5 {split_name} feature validation failed: dataset is empty.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError(f"Phase 5 {split_name} feature validation failed: null stock code found.")
    if df["invoice_day"].isna().any():
        raise ValueError(f"Phase 5 {split_name} feature validation failed: null invoice_day found.")
    if df[["daily_units", "lag1_units", "lag7_units", "rolling7_mean_units"]].isna().any().any():
        raise ValueError(
            f"Phase 5 {split_name} feature validation failed: null demand values found."
        )
    if (df[["daily_units", "lag1_units", "lag7_units", "rolling7_mean_units"]] < 0).any().any():
        raise ValueError(
            f"Phase 5 {split_name} feature validation failed: negative demand values found."
        )

    weekday_sum = df[PHASE5_WEEKDAY_COLUMNS].sum(axis=1)
    month_sum = df[PHASE5_MONTH_COLUMNS].sum(axis=1)
    if not (weekday_sum == 1).all():
        raise ValueError(
            f"Phase 5 {split_name} feature validation failed: weekday one-hot encoding invalid."
        )
    if not (month_sum == 1).all():
        raise ValueError(
            f"Phase 5 {split_name} feature validation failed: month one-hot encoding invalid."
        )

    missing_frozen_features = [col for col in PHASE5_FROZEN_FEATURE_COLUMNS if col not in df.columns]
    if missing_frozen_features:
        raise ValueError(
            f"Phase 5 {split_name} feature validation failed: missing frozen feature columns: {missing_frozen_features}"
        )


def validate_phase7_candidates(df: pd.DataFrame) -> None:
    ensure_required_columns(df, PHASE7_CANDIDATE_FROZEN_COLUMNS, "Phase 7 candidate simulation dataset")
    _validate_exact_columns(df, PHASE7_CANDIDATE_FROZEN_COLUMNS, "Phase 7 candidate simulation dataset")

    if df.empty:
        raise ValueError("Phase 7 candidate simulation validation failed: dataset is empty.")
    if df["invoice_day"].isna().any():
        raise ValueError("Phase 7 candidate simulation validation failed: null invoice_day found.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Phase 7 candidate simulation validation failed: null stock_code found.")
    if (df["candidate_price"] <= 0).any():
        raise ValueError("Phase 7 candidate simulation validation failed: non-positive candidate price found.")
    if (df["predicted_demand"] < 0).any():
        raise ValueError("Phase 7 candidate simulation validation failed: negative predicted demand found.")
    if (df["predicted_revenue"] < 0).any():
        raise ValueError("Phase 7 candidate simulation validation failed: negative predicted revenue found.")
    if (df["candidate_rank_by_revenue"] < 1).any():
        raise ValueError("Phase 7 candidate simulation validation failed: invalid candidate rank found.")


def validate_phase7_results(df: pd.DataFrame) -> None:
    ensure_required_columns(df, PHASE7_RESULT_FROZEN_COLUMNS, "Phase 7 simulation outcome dataset")
    _validate_exact_columns(df, PHASE7_RESULT_FROZEN_COLUMNS, "Phase 7 simulation outcome dataset")

    if df.empty:
        raise ValueError("Phase 7 simulation outcome validation failed: dataset is empty.")
    if df["invoice_day"].isna().any():
        raise ValueError("Phase 7 simulation outcome validation failed: null invoice_day found.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Phase 7 simulation outcome validation failed: null stock_code found.")
    if (df["base_price"] <= 0).any():
        raise ValueError("Phase 7 simulation outcome validation failed: non-positive base price found.")
    if (df["chosen_price"] <= 0).any():
        raise ValueError("Phase 7 simulation outcome validation failed: non-positive chosen price found.")
    if (df["previous_price"] <= 0).any():
        raise ValueError("Phase 7 simulation outcome validation failed: non-positive previous price found.")
    if not ((df["chosen_price"] - df["previous_price"]).round(12) == df["price_change"].round(12)).all():
        raise ValueError(
            "Phase 7 simulation outcome validation failed: price_change does not match chosen_price - previous_price."
        )
    if not ((df["price_change"].abs()).round(12) == df["abs_price_change"].round(12)).all():
        raise ValueError("Phase 7 simulation outcome validation failed: abs_price_change mismatch found.")
    if (df["abs_price_change"] < 0).any():
        raise ValueError("Phase 7 simulation outcome validation failed: negative abs_price_change found.")
    if (df["predicted_demand"] < 0).any():
        raise ValueError("Phase 7 simulation outcome validation failed: negative predicted demand found.")
    if (df["predicted_revenue"] < 0).any():
        raise ValueError("Phase 7 simulation outcome validation failed: negative predicted revenue found.")


def validate_phase11_metrics(df: pd.DataFrame) -> None:
    ensure_required_columns(df, PHASE11_METRIC_COLUMNS, "Phase 11 strategy metrics dataset")
    _validate_exact_columns(df, PHASE11_METRIC_COLUMNS, "Phase 11 strategy metrics dataset")

    if df.empty:
        raise ValueError("Phase 11 strategy metrics validation failed: dataset is empty.")
    if df[COL_STOCK_CODE].isna().any():
        raise ValueError("Phase 11 strategy metrics validation failed: null stock_code found.")
    if df["strategy"].isna().any() or (df["strategy"].astype("string").str.strip() == "").any():
        raise ValueError("Phase 11 strategy metrics validation failed: missing strategy found.")

    expected_strategies = set(PHASE7_STRATEGIES)
    actual_strategies = set(df["strategy"].astype(str).unique().tolist())
    if actual_strategies != expected_strategies:
        raise ValueError(
            "Phase 11 strategy metrics validation failed: strategy mismatch.\n"
            f"Expected strategies: {sorted(expected_strategies)}\n"
            f"Actual strategies:   {sorted(actual_strategies)}"
        )

    actual_metric_levels = set(df["metric_level"].astype(str).unique().tolist())
    expected_metric_levels = set(PHASE11_METRIC_LEVELS)
    if actual_metric_levels != expected_metric_levels:
        raise ValueError(
            "Phase 11 strategy metrics validation failed: metric_level mismatch.\n"
            f"Expected levels: {sorted(expected_metric_levels)}\n"
            f"Actual levels:   {sorted(actual_metric_levels)}"
        )

    metric_columns = list(PHASE11_SUMMARY_SCHEMA.keys())
    if df[metric_columns].isna().any().any():
        raise ValueError("Phase 11 strategy metrics validation failed: null summary metric value found.")


def validate_phase11_summary(summary_payload: object) -> None:
    if not isinstance(summary_payload, Mapping):
        raise ValueError(
            f"Phase 11 strategy summary validation failed: expected mapping, got {type(summary_payload).__name__}."
        )
    if not summary_payload:
        raise ValueError("Phase 11 strategy summary validation failed: payload is empty.")

    _validate_exact_keys(summary_payload, list(PHASE7_STRATEGIES), "Phase 11 strategy summary")
    for strategy_name in PHASE7_STRATEGIES:
        _validate_typed_mapping(
            summary_payload[strategy_name],
            PHASE11_SUMMARY_SCHEMA,
            f"Phase 11 strategy summary[{strategy_name}]",
        )


def validate_phase11_tests(statistical_payload: object) -> None:
    if not isinstance(statistical_payload, Mapping):
        raise ValueError(
            "Phase 11 statistical tests validation failed: "
            f"expected mapping, got {type(statistical_payload).__name__}."
        )
    if not statistical_payload:
        raise ValueError("Phase 11 statistical tests validation failed: payload is empty.")

    _validate_exact_keys(
        statistical_payload,
        list(PHASE11_TEST_SECTION_METRICS.keys()),
        "Phase 11 statistical tests",
    )

    expected_comparisons = list(PHASE11_COMPARISONS.keys())
    expected_tests = list(PHASE11_TEST_NAMES)
    for section_name in PHASE11_TEST_SECTION_METRICS:
        comparisons = statistical_payload[section_name]
        if not isinstance(comparisons, Mapping):
            raise ValueError(
                "Phase 11 statistical tests validation failed: "
                f"section '{section_name}' must be a mapping."
            )
        _validate_exact_keys(
            comparisons,
            expected_comparisons,
            f"Phase 11 statistical tests[{section_name}]",
        )

        for comparison_name in expected_comparisons:
            tests = comparisons[comparison_name]
            if not isinstance(tests, Mapping):
                raise ValueError(
                    "Phase 11 statistical tests validation failed: "
                    f"comparison '{comparison_name}' in section '{section_name}' must be a mapping."
                )
            _validate_exact_keys(
                tests,
                expected_tests,
                f"Phase 11 statistical tests[{section_name}][{comparison_name}]",
            )

            for test_name in expected_tests:
                test_values = tests[test_name]
                _validate_typed_mapping(
                    test_values,
                    PHASE11_TESTS_SCHEMA,
                    f"Phase 11 statistical tests[{section_name}][{comparison_name}][{test_name}]",
                )

                p_value = test_values["p_value"]
                sample_size = test_values["sample_size"]
                if not 0.0 <= p_value <= 1.0:
                    raise ValueError(
                        "Phase 11 statistical tests validation failed: "
                        f"p_value out of range in section '{section_name}', comparison '{comparison_name}', "
                        f"test '{test_name}'."
                    )
                if sample_size <= 0:
                    raise ValueError(
                        "Phase 11 statistical tests validation failed: "
                        f"non-positive sample_size in section '{section_name}', comparison '{comparison_name}', "
                        f"test '{test_name}'."
                    )


def validate_phase13_summary(validation_payload: object) -> None:
    context = "Phase 13 validation summary"
    if not isinstance(validation_payload, Mapping):
        raise ValueError(f"{context} validation failed: expected mapping, got {type(validation_payload).__name__}.")

    _validate_exact_keys(
        validation_payload,
        ["overall_passed", "baseline_summary", "parameter_variations", "rerun_consistency"],
        context,
    )
    _validate_scalar_type(validation_payload["overall_passed"], bool, f"{context}.overall_passed")
    validate_phase11_summary(validation_payload["baseline_summary"])

    parameter_variations = validation_payload["parameter_variations"]
    if not isinstance(parameter_variations, list):
        raise ValueError(f"{context}.parameter_variations validation failed: expected list.")
    if len(parameter_variations) != len(PHASE13_PARAMETER_VARIATIONS):
        raise ValueError(
            f"{context}.parameter_variations validation failed: expected {len(PHASE13_PARAMETER_VARIATIONS)} "
            f"items, got {len(parameter_variations)}."
        )

    for variation_payload, expected_variation in zip(parameter_variations, PHASE13_PARAMETER_VARIATIONS):
        if not isinstance(variation_payload, Mapping):
            raise ValueError(f"{context}.parameter_variations validation failed: each item must be a mapping.")

        variation_context = f"{context}.parameter_variations[{expected_variation['variation_name']}]"
        _validate_exact_keys(
            variation_payload,
            [
                "variation_name",
                "parameter_name",
                "parameter_value",
                "run_succeeded",
                "ml_highest_total_revenue",
                "hybrid_lowest_mean_absolute_change",
                "strategy_order_by_total_revenue",
                "strategy_order_by_mean_absolute_change",
                "error_message",
            ],
            variation_context,
        )

        _validate_scalar_type(variation_payload["variation_name"], str, f"{variation_context}.variation_name")
        _validate_scalar_type(variation_payload["parameter_name"], str, f"{variation_context}.parameter_name")
        _validate_scalar_type(variation_payload["parameter_value"], float, f"{variation_context}.parameter_value")
        _validate_scalar_type(variation_payload["run_succeeded"], bool, f"{variation_context}.run_succeeded")
        for ranking_check in PHASE13_RANKING_CHECKS:
            _validate_scalar_type(variation_payload[ranking_check], bool, f"{variation_context}.{ranking_check}")
        _validate_scalar_type(variation_payload["error_message"], str, f"{variation_context}.error_message")

        if variation_payload["variation_name"] != expected_variation["variation_name"]:
            raise ValueError(
                f"{variation_context} validation failed: expected variation_name "
                f"'{expected_variation['variation_name']}', got '{variation_payload['variation_name']}'."
            )
        if variation_payload["parameter_name"] != expected_variation["parameter_name"]:
            raise ValueError(
                f"{variation_context} validation failed: expected parameter_name "
                f"'{expected_variation['parameter_name']}', got '{variation_payload['parameter_name']}'."
            )
        if variation_payload["parameter_value"] != expected_variation["parameter_value"]:
            raise ValueError(
                f"{variation_context} validation failed: expected parameter_value "
                f"{expected_variation['parameter_value']}, got {variation_payload['parameter_value']}."
            )

        for field_name in ("strategy_order_by_total_revenue", "strategy_order_by_mean_absolute_change"):
            ranking = variation_payload[field_name]
            if not isinstance(ranking, list):
                raise ValueError(f"{variation_context}.{field_name} validation failed: expected list.")
            if ranking and ranking != list(PHASE7_STRATEGIES):
                if sorted(ranking) != sorted(PHASE7_STRATEGIES):
                    raise ValueError(
                        f"{variation_context}.{field_name} validation failed: expected a permutation of "
                        f"{list(PHASE7_STRATEGIES)}, got {ranking}."
                    )

    rerun_consistency = validation_payload["rerun_consistency"]
    if not isinstance(rerun_consistency, Mapping):
        raise ValueError(f"{context}.rerun_consistency validation failed: expected mapping.")

    rerun_context = f"{context}.rerun_consistency"
    _validate_exact_keys(
        rerun_consistency,
        ["run_succeeded", "metric_tolerance", "all_within_tolerance", "checks", "error_message"],
        rerun_context,
    )
    _validate_scalar_type(rerun_consistency["run_succeeded"], bool, f"{rerun_context}.run_succeeded")
    _validate_scalar_type(rerun_consistency["metric_tolerance"], float, f"{rerun_context}.metric_tolerance")
    _validate_scalar_type(rerun_consistency["all_within_tolerance"], bool, f"{rerun_context}.all_within_tolerance")
    _validate_scalar_type(rerun_consistency["error_message"], str, f"{rerun_context}.error_message")
    if rerun_consistency["metric_tolerance"] != PHASE13_RERUN_TOLERANCE:
        raise ValueError(
            f"{rerun_context}.metric_tolerance validation failed: expected {PHASE13_RERUN_TOLERANCE}, "
            f"got {rerun_consistency['metric_tolerance']}."
        )

    checks = rerun_consistency["checks"]
    if not isinstance(checks, list):
        raise ValueError(f"{rerun_context}.checks validation failed: expected list.")
    expected_check_count = len(PHASE7_STRATEGIES) * len(PHASE13_RERUN_METRICS)
    expected_lengths = {expected_check_count} if rerun_consistency["run_succeeded"] else {0, expected_check_count}
    if len(checks) not in expected_lengths:
        raise ValueError(
            f"{rerun_context}.checks validation failed: expected one of {sorted(expected_lengths)} "
            f"items, got {len(checks)}."
        )

    expected_pairs = {
        (strategy_name, metric_name) for strategy_name in PHASE7_STRATEGIES for metric_name in PHASE13_RERUN_METRICS
    }
    seen_pairs: set[tuple[str, str]] = set()
    for index, check_payload in enumerate(checks):
        check_context = f"{rerun_context}.checks[{index}]"
        if not isinstance(check_payload, Mapping):
            raise ValueError(f"{check_context} validation failed: expected mapping.")

        _validate_exact_keys(
            check_payload,
            [
                "strategy_name",
                "metric_name",
                "baseline_value",
                "rerun_value",
                "absolute_difference",
                "within_tolerance",
            ],
            check_context,
        )
        _validate_scalar_type(check_payload["strategy_name"], str, f"{check_context}.strategy_name")
        _validate_scalar_type(check_payload["metric_name"], str, f"{check_context}.metric_name")
        _validate_scalar_type(check_payload["baseline_value"], float, f"{check_context}.baseline_value")
        _validate_scalar_type(check_payload["rerun_value"], float, f"{check_context}.rerun_value")
        _validate_scalar_type(check_payload["absolute_difference"], float, f"{check_context}.absolute_difference")
        _validate_scalar_type(check_payload["within_tolerance"], bool, f"{check_context}.within_tolerance")

        pair = (check_payload["strategy_name"], check_payload["metric_name"])
        if pair not in expected_pairs:
            raise ValueError(
                f"{check_context} validation failed: unexpected (strategy_name, metric_name) pair {pair}."
            )
        seen_pairs.add(pair)

    if checks and seen_pairs != expected_pairs:
        raise ValueError(
            f"{rerun_context}.checks validation failed: missing expected pairs "
            f"{sorted(expected_pairs - seen_pairs)}."
        )
