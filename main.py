import argparse
import logging
from collections.abc import Callable

from config import SIMULATION_STRATEGIES
from pipeline.execution import (
    BUILD_GROUP,
    EVALUATE_COMMAND,
    SIMULATE_COMMAND,
    VALIDATE_COMMAND,
    command_logging_targets,
)
from pipeline.runner import run_all_simulations, run_build, run_evaluation, run_simulation, run_unit
from utils.logging_config import configure_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dynamic Pricing Study pipeline runner")
    parser.add_argument(
        "--build",
        action="store_true",
        help="Run the build command",
    )
    parser.add_argument(
        "--simulate",
        choices=[*SIMULATION_STRATEGIES, "all"],
        help="Run the simulation command for one strategy (rule|ml|hybrid) or all strategies (all)",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run the evaluation command on completed simulation outputs",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run the validation command for reproducibility checks",
    )
    args = parser.parse_args()
    if not args.build and args.simulate is None and not args.evaluate and not args.validate:
        parser.error("Specify one of --build, --simulate, --evaluate, or --validate.")
    return args


def _run_logged(
    *,
    logging_targets: tuple[str, ...],
    init_message: str,
    failure_message: str,
    success_message: str,
    success_output: str,
    runner: Callable[[], None],
) -> None:
    configure_logging(targets=logging_targets)
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
        logging_targets=command_logging_targets(EVALUATE_COMMAND),
        init_message="Dynamic Pricing Study runner initialised for the evaluation command.",
        failure_message="Evaluation command failed.",
        success_message="Evaluation command completed successfully.",
        success_output="Evaluation command completed successfully.",
        runner=run_evaluation,
    )


def _handle_validation() -> None:
    _run_logged(
        logging_targets=command_logging_targets(VALIDATE_COMMAND),
        init_message="Dynamic Pricing Study runner initialised for the validation command.",
        failure_message="Validation command failed.",
        success_message="Validation command completed successfully.",
        success_output="Validation command completed successfully.",
        runner=lambda: run_unit(VALIDATE_COMMAND),
    )


def _handle_single_strategy_simulation(strategy_name: str) -> None:
    _run_logged(
        logging_targets=command_logging_targets(SIMULATE_COMMAND),
        init_message=f"Dynamic Pricing Study runner initialised for the simulation command with strategy {strategy_name}.",
        failure_message=f"Simulation failed for strategy {strategy_name}.",
        success_message=f"Simulation completed successfully for strategy {strategy_name}.",
        success_output=f"Simulation for strategy '{strategy_name}' completed successfully.",
        runner=lambda: run_simulation(strategy_name=strategy_name),
    )


def _handle_all_strategy_simulations() -> None:
    _run_logged(
        logging_targets=command_logging_targets(SIMULATE_COMMAND),
        init_message="Dynamic Pricing Study runner initialised for the simulation command across all strategies.",
        failure_message="Simulation run failed while executing all strategies.",
        success_message="Simulation completed successfully for all strategies.",
        success_output="Simulation for all strategies completed successfully.",
        runner=run_all_simulations,
    )


def _handle_build_workflow(workflow_name: str) -> None:
    _run_logged(
        logging_targets=command_logging_targets(workflow_name),
        init_message="Dynamic Pricing Study runner initialised for the build workflow.",
        failure_message="Build workflow failed.",
        success_message="Build workflow completed successfully.",
        success_output="Build workflow completed successfully.",
        runner=run_build,
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

    _handle_build_workflow(BUILD_GROUP)


if __name__ == "__main__":
    main()
