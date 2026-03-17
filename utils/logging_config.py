import logging
from pathlib import Path

from config import (
    EXPERIMENT_LOG_FILE,
    LOGS_PATH,
    PHASE1_LOG_FILE,
    PHASE11_LOG_FILE,
    PHASE12_LOG_FILE,
    PHASE2_LOG_FILE,
    PHASE3_LOG_FILE,
    PHASE4_LOG_FILE,
    PHASE5_LOG_FILE,
    PHASE6_LOG_FILE,
    PHASE7_LOG_FILE,
    PROJECT_ROOT,
)


class LoggerPrefixFilter(logging.Filter):
    def __init__(self, prefixes: tuple[str, ...]) -> None:
        super().__init__()
        self.prefixes = prefixes

    def filter(self, record: logging.LogRecord) -> bool:
        return any(record.name.startswith(prefix) for prefix in self.prefixes)


def _logs_dir() -> Path:
    return Path(PROJECT_ROOT).resolve() / LOGS_PATH


def _experiment_handler(logs_dir: Path) -> logging.Handler:
    handler = logging.FileHandler(logs_dir / EXPERIMENT_LOG_FILE, mode="a")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    return handler


def _phase_handler_specs() -> tuple[tuple[int, str, tuple[str, ...]], ...]:
    return (
        (1, PHASE1_LOG_FILE, ("preprocessing.raw_inspection",)),
        (2, PHASE2_LOG_FILE, ("preprocessing.clean_data",)),
        (3, PHASE3_LOG_FILE, ("preprocessing.select_products",)),
        (4, PHASE4_LOG_FILE, ("preprocessing.aggregate_daily",)),
        (5, PHASE5_LOG_FILE, ("preprocessing.feature_engineering",)),
        (6, PHASE6_LOG_FILE, ("models.demand_model",)),
        (7, PHASE7_LOG_FILE, ("simulation.simulator",)),
        (11, PHASE11_LOG_FILE, ("evaluation.metrics", "evaluation.statistical_tests", "utils.simulation_artifacts")),
        (12, PHASE12_LOG_FILE, ("dashboard.app",)),
    )


def _phase_handler(logs_dir: Path, log_file_name: str, logger_prefixes: tuple[str, ...]) -> logging.Handler:
    handler = logging.FileHandler(logs_dir / log_file_name, mode="a")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    handler.addFilter(LoggerPrefixFilter(logger_prefixes))
    return handler


def configure_logging(phases: list[int] | None = None) -> None:
    logs_dir = _logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    root_logger.addHandler(_experiment_handler(logs_dir))

    selected_phases = set(phases or [])

    for phase_number, log_file_name, logger_prefixes in _phase_handler_specs():
        if phase_number in selected_phases:
            root_logger.addHandler(_phase_handler(logs_dir, log_file_name, logger_prefixes))
