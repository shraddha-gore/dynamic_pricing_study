import logging
from pathlib import Path

from config import (
    BUILD_GROUP,
    DASHBOARD_COMMAND,
    EVALUATE_COMMAND,
    SIMULATE_COMMAND,
    MASTER_LOG_FILE,
    LOGS_PATH,
    BUILD_LOG_FILE,
    DASHBOARD_LOG_FILE,
    EVALUATION_LOG_FILE,
    SIMULATION_LOG_FILE,
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


def _master_handler(logs_dir: Path) -> logging.Handler:
    handler = logging.FileHandler(logs_dir / MASTER_LOG_FILE, mode="a")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    return handler


def _logging_handler_specs() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    return (
        (
            BUILD_GROUP,
            BUILD_LOG_FILE,
            (
                "preprocessing.raw_inspection",
                "preprocessing.clean_data",
                "preprocessing.select_products",
                "preprocessing.aggregate_daily",
                "preprocessing.feature_engineering",
                "models.demand_model",
            ),
        ),
        (SIMULATE_COMMAND, SIMULATION_LOG_FILE, ("simulation.simulator",)),
        (EVALUATE_COMMAND, EVALUATION_LOG_FILE, ("evaluation.metrics", "evaluation.statistical_tests", "utils.simulation_artifacts")),
        (DASHBOARD_COMMAND, DASHBOARD_LOG_FILE, ("dashboard.app",)),
    )


def _target_handler(logs_dir: Path, log_file_name: str, logger_prefixes: tuple[str, ...]) -> logging.Handler:
    handler = logging.FileHandler(logs_dir / log_file_name, mode="a")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    handler.addFilter(LoggerPrefixFilter(logger_prefixes))
    return handler


def configure_logging(targets: list[str] | tuple[str, ...] | None = None) -> None:
    logs_dir = _logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    root_logger.addHandler(_master_handler(logs_dir))

    selected_targets = set(targets or [])

    for target_name, log_file_name, logger_prefixes in _logging_handler_specs():
        if target_name in selected_targets:
            root_logger.addHandler(_target_handler(logs_dir, log_file_name, logger_prefixes))
