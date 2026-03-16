import argparse
import logging

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
        "--phase",
        type=int,
        help="Optional specific phase to run (for debugging/development)",
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
    return parser.parse_args()


def run_phase11_evaluation() -> None:
    from evaluation.metrics import compute_metrics
    from evaluation.statistical_tests import run_tests

    compute_metrics()
    run_tests()


def main() -> None:
    args = parse_args()
    if args.evaluate:
        configure_logging(phases=[11])
        logging.info("Dynamic Pricing Study runner initialised for Phase 11 evaluation.")
        try:
            run_phase11_evaluation()
        except Exception:
            logging.exception("Phase 11 evaluation failed.")
            raise
        logging.info("Phase 11 evaluation completed successfully.")
        print("Phase 11 evaluation completed successfully.")
        return

    if args.simulate is not None and args.simulate != "all":
        from simulation.simulator import run_phase7

        configure_logging(phases=[7])
        logging.info("Dynamic Pricing Study runner initialised for simulation strategy %s.", args.simulate)
        try:
            run_phase7(strategy_name=args.simulate)
        except Exception:
            logging.exception("Simulation failed for strategy %s.", args.simulate)
            raise
        logging.info("Simulation completed successfully for strategy %s.", args.simulate)
        print(f"Simulation for strategy '{args.simulate}' completed successfully.")
        return

    if args.simulate == "all":
        from simulation.simulator import run_phase7

        configure_logging(phases=[7])
        logging.info("Dynamic Pricing Study runner initialised for all simulation strategies.")
        for strategy in PHASE7_STRATEGIES:
            try:
                run_phase7(strategy_name=strategy)
            except Exception:
                logging.exception("Simulation failed for strategy %s.", strategy)
                raise
        logging.info("Simulation completed successfully for all strategies.")
        print("Simulation for all strategies completed successfully.")
        return

    if args.phase is not None:
        from pipeline.runner import available_phases, run_phase

        if args.phase not in available_phases():
            raise ValueError(f"Unsupported phase: {args.phase}")

        configure_logging(phases=[args.phase])
        logging.info("Dynamic Pricing Study runner initialised for phase %s.", args.phase)
        try:
            run_phase(args.phase)
        except Exception:
            logging.exception("Phase %s failed.", args.phase)
            raise
        logging.info("Phase %s completed successfully.", args.phase)
        print(f"Phase {args.phase} completed successfully.")
        return

    from pipeline.runner import run_workflow

    from pipeline.runner import available_phases

    phases = available_phases()
    configure_logging(phases=phases)
    logging.info("Dynamic Pricing Study runner initialised for full workflow.")
    try:
        run_workflow()
    except Exception:
        logging.exception("Full workflow failed.")
        raise
    logging.info("Full workflow completed successfully.")
    print("Full workflow completed successfully.")

if __name__ == "__main__":
    main()
