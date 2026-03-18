import argparse
import logging
from collections.abc import Callable

from config import PHASE7_STRATEGIES
from utils.logging_config import configure_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dynamic Pricing Study pipeline runner")
    parser.add_argument(
        "--workflow",
        choices=["full"],
        default="full",
        help="Workflow mode (default: full)",
    )
    parser.add_argument(
        "--simulate",
        choices=[*PHASE7_STRATEGIES, "all"],
        help="Run Phase 7 simulation for one strategy (rule|ml|hybrid) or all strategies (all)",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run Phase 11 evaluation on completed simulation outputs",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run Phase 13 system validation and reproducibility checks",
    )
    return parser.parse_args()


def run_phase11_evaluation() -> None:
    from evaluation.metrics import compute_metrics
    from evaluation.statistical_tests import run_tests

    compute_metrics()
    run_tests()


def _run_logged(
    *,
    phases: list[int],
    init_message: str,
    failure_message: str,
    success_message: str,
    success_output: str,
    runner: Callable[[], None],
) -> None:
    configure_logging(phases=phases)
    logging.info(init_message)
    try:
        runner()
    except Exception:
        logging.exception(failure_message)
        raise
    logging.info(success_message)
    print(success_output)


def _handle_evaluation() -> None:
    _run_logged(
        phases=[11],
        init_message="Dynamic Pricing Study runner initialised for Phase 11 evaluation.",
        failure_message="Phase 11 evaluation failed.",
        success_message="Phase 11 evaluation completed successfully.",
        success_output="Phase 11 evaluation completed successfully.",
        runner=run_phase11_evaluation,
    )


def _handle_validation() -> None:
    from evaluation.validation import run_phase13

    _run_logged(
        phases=[13],
        init_message="Dynamic Pricing Study runner initialised for Phase 13 validation.",
        failure_message="Phase 13 validation failed.",
        success_message="Phase 13 validation completed successfully.",
        success_output="Phase 13 validation completed successfully.",
        runner=run_phase13,
    )


def _handle_single_strategy_simulation(strategy_name: str) -> None:
    from simulation.simulator import run_phase7

    _run_logged(
        phases=[7],
        init_message=f"Dynamic Pricing Study runner initialised for simulation strategy {strategy_name}.",
        failure_message=f"Simulation failed for strategy {strategy_name}.",
        success_message=f"Simulation completed successfully for strategy {strategy_name}.",
        success_output=f"Simulation for strategy '{strategy_name}' completed successfully.",
        runner=lambda: run_phase7(strategy_name=strategy_name),
    )


def _handle_all_strategy_simulations() -> None:
    from simulation.simulator import run_phase7

    def run_all_simulations() -> None:
        for strategy_name in PHASE7_STRATEGIES:
            try:
                run_phase7(strategy_name=strategy_name)
            except Exception as exc:
                raise RuntimeError(f"Simulation failed for strategy {strategy_name}.") from exc

    _run_logged(
        phases=[7],
        init_message="Dynamic Pricing Study runner initialised for all simulation strategies.",
        failure_message="Simulation run failed while executing all strategies.",
        success_message="Simulation completed successfully for all strategies.",
        success_output="Simulation for all strategies completed successfully.",
        runner=run_all_simulations,
    )


def _handle_full_workflow() -> None:
    from pipeline.runner import run_workflow, workflow_phases

    _run_logged(
        phases=workflow_phases(),
        init_message="Dynamic Pricing Study runner initialised for full workflow.",
        failure_message="Full workflow failed.",
        success_message="Full workflow completed successfully.",
        success_output="Full workflow completed successfully.",
        runner=run_workflow,
    )


def main() -> None:
    args = parse_args()
    if args.evaluate:
        _handle_evaluation()
        return

    if args.simulate is not None and args.simulate != "all":
        _handle_single_strategy_simulation(args.simulate)
        return

    if args.simulate == "all":
        _handle_all_strategy_simulations()
        return

    if args.validate:
        _handle_validation()
        return

    _handle_full_workflow()

if __name__ == "__main__":
    main()
