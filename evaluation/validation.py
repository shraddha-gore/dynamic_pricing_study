import json
import logging
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import strategies.hybrid_pricing as hybrid_pricing
from config import (
    PHASE11_STATISTICAL_TESTS_PATH,
    PHASE11_STRATEGY_METRICS_PATH,
    PHASE11_STRATEGY_SUMMARY_PATH,
    PHASE13_PARAMETER_VARIATIONS,
    PHASE13_RERUN_METRICS,
    PHASE13_RERUN_TOLERANCE,
    PHASE13_VALIDATION_SUMMARY_PATH,
    PHASE7_STRATEGIES,
    PROJECT_ROOT,
    SIMULATION_CANDIDATE_PATHS,
    SIMULATION_RESULTS_PATHS,
)
from evaluation.metrics import compute_metrics
from evaluation.statistical_tests import run_tests
from preprocessing.common import configured_path, configured_path_from_map
from simulation.simulator import run_phase7
from utils.data_contracts import validate_phase11_summary, validate_phase13_summary

logger = logging.getLogger(__name__)


def _baseline_summary_path() -> Path:
    return configured_path(PROJECT_ROOT, PHASE11_STRATEGY_SUMMARY_PATH)


def _validation_output_path() -> Path:
    return configured_path(PROJECT_ROOT, PHASE13_VALIDATION_SUMMARY_PATH)


def _managed_artifact_paths() -> list[Path]:
    paths = [
        configured_path(PROJECT_ROOT, PHASE11_STRATEGY_METRICS_PATH),
        configured_path(PROJECT_ROOT, PHASE11_STRATEGY_SUMMARY_PATH),
        configured_path(PROJECT_ROOT, PHASE11_STATISTICAL_TESTS_PATH),
    ]
    for strategy_name in PHASE7_STRATEGIES:
        paths.append(configured_path_from_map(PROJECT_ROOT, SIMULATION_CANDIDATE_PATHS, strategy_name))
        paths.append(configured_path_from_map(PROJECT_ROOT, SIMULATION_RESULTS_PATHS, strategy_name))
    return paths


@contextmanager
def _preserve_phase_artifacts(paths: list[Path]) -> Iterator[None]:
    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        snapshot_records: list[tuple[Path, bool, Path]] = []

        for index, artifact_path in enumerate(paths):
            snapshot_path = temp_dir / f"artifact_{index}"
            existed = artifact_path.exists()
            if existed:
                shutil.copy2(artifact_path, snapshot_path)
            snapshot_records.append((artifact_path, existed, snapshot_path))

        try:
            yield
        finally:
            for artifact_path, existed, snapshot_path in snapshot_records:
                if existed:
                    artifact_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(snapshot_path, artifact_path)
                elif artifact_path.exists():
                    artifact_path.unlink()


@contextmanager
def _temporary_hybrid_override(parameter_name: str, parameter_value: float) -> Iterator[None]:
    if not hasattr(hybrid_pricing, parameter_name):
        raise AttributeError(f"Unknown hybrid pricing parameter override requested: {parameter_name}")

    original_value = getattr(hybrid_pricing, parameter_name)
    setattr(hybrid_pricing, parameter_name, parameter_value)
    try:
        yield
    finally:
        setattr(hybrid_pricing, parameter_name, original_value)


def _load_phase11_summary(summary_path: Path) -> dict[str, dict[str, float]]:
    if not summary_path.exists():
        raise FileNotFoundError(f"Phase 13 baseline summary not found: {summary_path}")

    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    validate_phase11_summary(summary_payload)
    return summary_payload


def _run_all_simulations_and_evaluation() -> dict[str, dict[str, float]]:
    for strategy_name in PHASE7_STRATEGIES:
        logger.info("Phase 13 re-executing Phase 7 for strategy: %s", strategy_name)
        run_phase7(strategy_name=strategy_name)

    logger.info("Phase 13 re-executing Phase 11 metrics.")
    _, summary = compute_metrics()
    logger.info("Phase 13 re-executing Phase 11 statistical tests.")
    run_tests()
    validate_phase11_summary(summary)
    return summary


def _rank_strategies(
    summary_payload: dict[str, dict[str, float]],
    metric_name: str,
    *,
    ascending: bool,
) -> list[str]:
    sort_multiplier = 1.0 if ascending else -1.0
    ranked_items = sorted(
        summary_payload.items(),
        key=lambda item: (sort_multiplier * float(item[1][metric_name]), item[0]),
    )
    return [strategy_name for strategy_name, _ in ranked_items]


def _run_parameter_variation(
    variation_name: str,
    parameter_name: str,
    parameter_value: float,
) -> dict[str, object]:
    logger.info(
        "Phase 13 parameter variation started: %s | %s=%s",
        variation_name,
        parameter_name,
        parameter_value,
    )

    variation_result: dict[str, object] = {
        "variation_name": variation_name,
        "parameter_name": parameter_name,
        "parameter_value": float(parameter_value),
        "run_succeeded": False,
        "ml_highest_total_revenue": False,
        "hybrid_lowest_mean_absolute_change": False,
        "strategy_order_by_total_revenue": [],
        "strategy_order_by_mean_absolute_change": [],
        "error_message": "",
    }

    try:
        with _temporary_hybrid_override(parameter_name, parameter_value):
            summary_payload = _run_all_simulations_and_evaluation()

        revenue_ranking = _rank_strategies(summary_payload, "total_revenue", ascending=False)
        stability_ranking = _rank_strategies(summary_payload, "mean_absolute_change", ascending=True)

        variation_result.update(
            {
                "run_succeeded": True,
                "ml_highest_total_revenue": revenue_ranking[0] == "ml",
                "hybrid_lowest_mean_absolute_change": stability_ranking[0] == "hybrid",
                "strategy_order_by_total_revenue": revenue_ranking,
                "strategy_order_by_mean_absolute_change": stability_ranking,
            }
        )
        logger.info(
            "Phase 13 parameter variation completed: %s | revenue ranking=%s | stability ranking=%s",
            variation_name,
            revenue_ranking,
            stability_ranking,
        )
    except Exception as exc:
        variation_result["error_message"] = str(exc)
        logger.exception("Phase 13 parameter variation failed: %s", variation_name)

    return variation_result


def _run_rerun_consistency_check(
    baseline_summary: dict[str, dict[str, float]],
) -> dict[str, object]:
    logger.info("Phase 13 re-run consistency check started.")

    rerun_result: dict[str, object] = {
        "run_succeeded": False,
        "metric_tolerance": float(PHASE13_RERUN_TOLERANCE),
        "all_within_tolerance": False,
        "checks": [],
        "error_message": "",
    }

    try:
        regenerated_summary = _run_all_simulations_and_evaluation()
        checks: list[dict[str, object]] = []

        for strategy_name in PHASE7_STRATEGIES:
            for metric_name in PHASE13_RERUN_METRICS:
                baseline_value = float(baseline_summary[strategy_name][metric_name])
                rerun_value = float(regenerated_summary[strategy_name][metric_name])
                absolute_difference = abs(rerun_value - baseline_value)
                checks.append(
                    {
                        "strategy_name": strategy_name,
                        "metric_name": metric_name,
                        "baseline_value": baseline_value,
                        "rerun_value": rerun_value,
                        "absolute_difference": float(absolute_difference),
                        "within_tolerance": absolute_difference < PHASE13_RERUN_TOLERANCE,
                    }
                )

        rerun_result.update(
            {
                "run_succeeded": True,
                "all_within_tolerance": all(check["within_tolerance"] for check in checks),
                "checks": checks,
            }
        )
        logger.info(
            "Phase 13 re-run consistency check completed | all_within_tolerance=%s",
            rerun_result["all_within_tolerance"],
        )
    except Exception as exc:
        rerun_result["error_message"] = str(exc)
        logger.exception("Phase 13 re-run consistency check failed.")

    return rerun_result


def _overall_passed(
    parameter_variations: list[dict[str, object]],
    rerun_consistency: dict[str, object],
) -> bool:
    variations_passed = all(
        bool(variation["run_succeeded"])
        and bool(variation["ml_highest_total_revenue"])
        and bool(variation["hybrid_lowest_mean_absolute_change"])
        for variation in parameter_variations
    )
    return variations_passed and bool(rerun_consistency["run_succeeded"]) and bool(
        rerun_consistency["all_within_tolerance"]
    )


def run_phase13() -> dict[str, object]:
    logger.info("Phase 13 validation started.")
    baseline_summary = _load_phase11_summary(_baseline_summary_path())

    with _preserve_phase_artifacts(_managed_artifact_paths()):
        parameter_variations = [
            _run_parameter_variation(
                variation_name=str(variation["variation_name"]),
                parameter_name=str(variation["parameter_name"]),
                parameter_value=float(variation["parameter_value"]),
            )
            for variation in PHASE13_PARAMETER_VARIATIONS
        ]
        rerun_consistency = _run_rerun_consistency_check(baseline_summary)

    validation_payload = {
        "overall_passed": _overall_passed(parameter_variations, rerun_consistency),
        "baseline_summary": baseline_summary,
        "parameter_variations": parameter_variations,
        "rerun_consistency": rerun_consistency,
    }
    validate_phase13_summary(validation_payload)

    output_path = _validation_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(validation_payload, indent=2), encoding="utf-8")

    logger.info(
        "Phase 13 validation completed successfully. overall_passed=%s | output=%s",
        validation_payload["overall_passed"],
        output_path,
    )
    return validation_payload
