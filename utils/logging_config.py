import logging
from pathlib import Path

from config import EXPERIMENT_LOG_FILE, LOGS_PATH, PHASE1_LOG_FILE, PROJECT_ROOT


def configure_logging(phases: list[int] | None = None) -> None:
    project_root = Path(PROJECT_ROOT).resolve()
    logs_dir = project_root / LOGS_PATH
    logs_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    experiment_handler = logging.FileHandler(logs_dir / EXPERIMENT_LOG_FILE, mode="a")
    experiment_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    root_logger.addHandler(experiment_handler)

    selected_phases = set(phases or [])

    if 1 in selected_phases:
        phase_handler = logging.FileHandler(logs_dir / PHASE1_LOG_FILE, mode="a")
        phase_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        root_logger.addHandler(phase_handler)
