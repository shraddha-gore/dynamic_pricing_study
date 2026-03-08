import argparse
import logging

from config import PHASE7_STRATEGIES
from pipeline.runner import available_phases, run_phase, run_workflow
from simulation.simulator import run_phase7
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
        choices=available_phases(),
        help="Optional specific phase to run (for debugging/development)",
    )
    parser.add_argument(
        "--simulate",
        choices=[*PHASE7_STRATEGIES, "all"],
        help="Run Phase 7 simulation for one strategy (rule|ml|hybrid) or all strategies (all)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.simulate is not None and args.simulate != "all":
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
