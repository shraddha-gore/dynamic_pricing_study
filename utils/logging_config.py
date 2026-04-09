import logging
from pathlib import Path

from config import (
    AGGREGATE_DAILY_UNIT,
    CLEAN_UNIT,
    DASHBOARD_COMMAND,
    EVALUATE_COMMAND,
    FEATURE_ENGINEERING_UNIT,
    INSPECT_UNIT,
    SELECT_PRODUCTS_UNIT,
    SIMULATE_COMMAND,
    TRAIN_MODEL_UNIT,
    VALIDATE_COMMAND,
    EXPERIMENT_LOG_FILE,
    LOGS_PATH,
    RAW_INSPECTION_LOG_FILE,
    EVALUATION_LOG_FILE,
    DASHBOARD_LOG_FILE,
    VALIDATION_LOG_FILE,
    CLEANING_LOG_FILE,
    PRODUCT_SELECTION_LOG_FILE,
    DAILY_AGGREGATION_LOG_FILE,
    FEATURE_ENGINEERING_LOG_FILE,
    MODEL_TRAINING_LOG_FILE,
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


def _experiment_handler(logs_dir: Path) -> logging.Handler:
    handler = logging.FileHandler(logs_dir / EXPERIMENT_LOG_FILE, mode="a")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    return handler


def _logging_handler_specs() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    return (
        (INSPECT_UNIT, RAW_INSPECTION_LOG_FILE, ("preprocessing.raw_inspection",)),
        (CLEAN_UNIT, CLEANING_LOG_FILE, ("preprocessing.clean_data",)),
        (SELECT_PRODUCTS_UNIT, PRODUCT_SELECTION_LOG_FILE, ("preprocessing.select_products",)),
        (AGGREGATE_DAILY_UNIT, DAILY_AGGREGATION_LOG_FILE, ("preprocessing.aggregate_daily",)),
        (FEATURE_ENGINEERING_UNIT, FEATURE_ENGINEERING_LOG_FILE, ("preprocessing.feature_engineering",)),
        (TRAIN_MODEL_UNIT, MODEL_TRAINING_LOG_FILE, ("models.demand_model",)),
        (SIMULATE_COMMAND, SIMULATION_LOG_FILE, ("simulation.simulator",)),
        (EVALUATE_COMMAND, EVALUATION_LOG_FILE, ("evaluation.metrics", "evaluation.statistical_tests", "utils.simulation_artifacts")),
        (DASHBOARD_COMMAND, DASHBOARD_LOG_FILE, ("dashboard.app",)),
        (
            VALIDATE_COMMAND,
            VALIDATION_LOG_FILE,
            (
                "evaluation.validation",
                "simulation.simulator",
                "evaluation.metrics",
                "evaluation.statistical_tests",
                "utils.simulation_artifacts",
            ),
        ),
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

    root_logger.addHandler(_experiment_handler(logs_dir))

    selected_targets = set(targets or [])

    for target_name, log_file_name, logger_prefixes in _logging_handler_specs():
        if target_name in selected_targets:
            root_logger.addHandler(_target_handler(logs_dir, log_file_name, logger_prefixes))
