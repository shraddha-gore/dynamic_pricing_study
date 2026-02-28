import argparse
import logging

from pipeline.runner import available_phases, run_phase, run_workflow
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
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
