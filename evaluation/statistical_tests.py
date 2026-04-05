import json
import logging

import numpy as np
import pandas as pd
from scipy.stats import ttest_rel, wilcoxon

from config import EVALUATION_COMPARISONS, EVALUATION_PAIRING_KEYS, EVALUATION_STATISTICAL_TESTS_PATH, PROJECT_ROOT
from preprocessing.common import configured_path
from utils.simulation_artifacts import load_strategy_results

logger = logging.getLogger(__name__)


def _test_output_path():
    return configured_path(PROJECT_ROOT, EVALUATION_STATISTICAL_TESTS_PATH)


def _align_results(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    left_strategy: str,
    right_strategy: str,
) -> pd.DataFrame:
    aligned_df = left_df.merge(
        right_df,
        on=EVALUATION_PAIRING_KEYS,
        how="inner",
        suffixes=(f"_{left_strategy}", f"_{right_strategy}"),
    )

    if len(aligned_df) != len(left_df) or len(aligned_df) != len(right_df):
        raise ValueError(
            f"Evaluation statistical testing alignment failed for '{left_strategy}' vs '{right_strategy}'."
        )

    return aligned_df.sort_values(EVALUATION_PAIRING_KEYS, kind="mergesort").reset_index(drop=True)


def _serialise_test_result(statistic: float, p_value: float, sample_size: int) -> dict[str, float | int]:
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "sample_size": int(sample_size),
    }


def _run_paired_tests(left_values: pd.Series, right_values: pd.Series) -> dict[str, dict[str, float | int]]:
    left_array = left_values.to_numpy(dtype=float)
    right_array = right_values.to_numpy(dtype=float)
    sample_size = len(left_array)

    if sample_size == 0:
        raise ValueError("Evaluation statistical testing failed: no paired observations available.")

    differences = left_array - right_array
    if np.allclose(differences, 0.0):
        neutral_result = _serialise_test_result(0.0, 1.0, sample_size)
        return {
            "paired_ttest": neutral_result,
            "wilcoxon": neutral_result,
        }

    paired_ttest = ttest_rel(left_array, right_array)
    wilcoxon_result = wilcoxon(left_array, right_array)

    return {
        "paired_ttest": _serialise_test_result(paired_ttest.statistic, paired_ttest.pvalue, sample_size),
        "wilcoxon": _serialise_test_result(wilcoxon_result.statistic, wilcoxon_result.pvalue, sample_size),
    }


def _comparison_test_results(
    aligned_df: pd.DataFrame,
    left_strategy: str,
    right_strategy: str,
) -> dict[str, dict[str, dict[str, float | int]]]:
    return {
        "revenue": _run_paired_tests(
            aligned_df[f"predicted_revenue_{left_strategy}"],
            aligned_df[f"predicted_revenue_{right_strategy}"],
        ),
        "stability": _run_paired_tests(
            aligned_df[f"abs_price_change_{left_strategy}"],
            aligned_df[f"abs_price_change_{right_strategy}"],
        ),
    }


def run_tests() -> dict[str, dict[str, dict[str, dict[str, float | int]]]]:
    logger.info("Evaluation statistical testing started.")
    results_by_strategy = load_strategy_results()

    statistical_results = {
        "revenue_tests": {},
        "stability_tests": {},
    }

    for comparison_name, (left_strategy, right_strategy) in EVALUATION_COMPARISONS.items():
        aligned_df = _align_results(
            results_by_strategy[left_strategy],
            results_by_strategy[right_strategy],
            left_strategy,
            right_strategy,
        )
        comparison_results = _comparison_test_results(aligned_df, left_strategy, right_strategy)
        statistical_results["revenue_tests"][comparison_name] = comparison_results["revenue"]
        statistical_results["stability_tests"][comparison_name] = comparison_results["stability"]

    output_path = _test_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(statistical_results, indent=2), encoding="utf-8")

    logger.info("Evaluation statistical tests written successfully to %s", output_path)
    return statistical_results
