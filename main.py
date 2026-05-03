import argparse
import logging
from collections.abc import Callable

from config import BUILD_GROUP, EVALUATE_COMMAND, SIMULATE_COMMAND
from pipeline.execution import (
    command_logging_targets,
)
from pipeline.runner import run_all_simulations, run_build, run_evaluation
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
        action="store_true",
        help="Run the simulation command across all strategies",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run the evaluation command on completed simulation outputs",
    )
    parser.add_argument(
        "--run-pipeline",
        action="store_true",
        help="Run build, simulate, and evaluate in sequence",
    )
    args = parser.parse_args()
    if not args.build and not args.simulate and not args.evaluate and not args.run_pipeline:
        parser.error("Specify one of --run-pipeline, --build, --simulate, or --evaluate.")
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
    if success_output:
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


def _handle_simulations() -> None:
    _run_logged(
        logging_targets=command_logging_targets(SIMULATE_COMMAND),
        init_message="Dynamic Pricing Study runner initialised for the simulation command across all strategies.",
        failure_message="Simulation run failed while executing all strategies.",
        success_message="Simulation completed successfully for all strategies.",
        success_output="Simulation for all strategies (rule, ml, hybrid) completed successfully.",
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


def _handle_run_pipeline() -> None:
    _run_logged(
        logging_targets=command_logging_targets(BUILD_GROUP),
        init_message="Dynamic Pricing Study runner initialised for the build workflow.",
        failure_message="Build workflow failed.",
        success_message="Build workflow completed successfully.",
        success_output="",
        runner=run_build,
    )
    _run_logged(
        logging_targets=command_logging_targets(SIMULATE_COMMAND),
        init_message="Dynamic Pricing Study runner initialised for the simulation command across all strategies.",
        failure_message="Simulation run failed while executing all strategies.",
        success_message="Simulation completed successfully for all strategies.",
        success_output="",
        runner=run_all_simulations,
    )
    _run_logged(
        logging_targets=command_logging_targets(EVALUATE_COMMAND),
        init_message="Dynamic Pricing Study runner initialised for the evaluation command.",
        failure_message="Evaluation command failed.",
        success_message="Evaluation command completed successfully.",
        success_output="",
        runner=run_evaluation,
    )
    print("Full pipeline completed successfully: build, simulate (rule, ml, hybrid), and evaluate.")


def main() -> None:
    args = parse_args()
    if args.run_pipeline:
        _handle_run_pipeline()
        return

    if args.evaluate:
        _handle_evaluation()
        return

    if args.simulate:
        _handle_simulations()
        return

    _handle_build_workflow(BUILD_GROUP)


if __name__ == "__main__":
    main()
