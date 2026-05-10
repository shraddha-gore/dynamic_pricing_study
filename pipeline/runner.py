"""Dispatches each pipeline stage in sequence and wires simulation strategies to their runners."""

from collections.abc import Callable

from config import (
    AGGREGATE_DAILY_UNIT,
    BUILD_GROUP,
    CLEAN_UNIT,
    EVALUATE_COMMAND,
    FEATURE_ENGINEERING_UNIT,
    INSPECT_UNIT,
    SELECT_PRODUCTS_UNIT,
    SIMULATION_STRATEGIES,
    TRAIN_MODEL_UNIT,
)
from models.demand_model import run_demand_model_training
from pipeline.execution import group_units
from preprocessing.aggregate_daily import run_aggregate_daily
from preprocessing.clean_data import run_clean_data
from preprocessing.feature_engineering import run_feature_engineering
from preprocessing.raw_inspection import run_raw_inspection
from preprocessing.select_products import run_select_products


def run_evaluation() -> None:
    from evaluation.metrics import compute_metrics
    from evaluation.statistical_tests import run_tests

    compute_metrics()
    run_tests()


def run_simulation(strategy_name: str) -> None:
    from simulation.simulator import run_simulation

    run_simulation(strategy_name=strategy_name)


def run_all_simulations() -> None:
    for strategy_name in SIMULATION_STRATEGIES:
        try:
            run_simulation(strategy_name=strategy_name)
        except Exception as exc:
            raise RuntimeError(f"Simulation failed for strategy {strategy_name}.") from exc


def _unit_registry() -> tuple[tuple[str, Callable[[], None]], ...]:
    # Ordered tuple rather than a dict so unit execution order is explicit and unambiguous.
    return (
        (INSPECT_UNIT, run_raw_inspection),
        (CLEAN_UNIT, run_clean_data),
        (SELECT_PRODUCTS_UNIT, run_select_products),
        (AGGREGATE_DAILY_UNIT, run_aggregate_daily),
        (FEATURE_ENGINEERING_UNIT, run_feature_engineering),
        (TRAIN_MODEL_UNIT, run_demand_model_training),
        (EVALUATE_COMMAND, run_evaluation),
    )


def _unit_lookup() -> dict[str, Callable[[], None]]:
    return dict(_unit_registry())


def run_unit(unit_name: str) -> None:
    unit_lookup = _unit_lookup()
    if unit_name not in unit_lookup:
        raise ValueError(f"Unsupported execution unit: {unit_name}")
    unit_lookup[unit_name]()


def available_units() -> list[str]:
    return [unit_name for unit_name, _ in _unit_registry()]


def run_group(group_name: str) -> None:
    for unit_name in group_units(group_name):
        run_unit(unit_name)


def available_groups() -> list[str]:
    return [BUILD_GROUP]


def build_units() -> tuple[str, ...]:
    return group_units(BUILD_GROUP)


def run_build() -> None:
    run_group(BUILD_GROUP)
