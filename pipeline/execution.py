from config import (
    AGGREGATE_DAILY_UNIT,
    BUILD_GROUP,
    BUILD_UNITS,
    CLEAN_UNIT,
    COMMAND_LOGGING_TARGETS,
    DASHBOARD_COMMAND,
    EVALUATE_COMMAND,
    FEATURE_ENGINEERING_UNIT,
    GROUP_UNITS,
    INSPECT_UNIT,
    SELECT_PRODUCTS_UNIT,
    SIMULATE_COMMAND,
    TRAIN_MODEL_UNIT,
    VALIDATE_COMMAND,
)


def available_groups() -> tuple[str, ...]:
    return tuple(GROUP_UNITS)


def group_units(group_name: str) -> tuple[str, ...]:
    if group_name not in GROUP_UNITS:
        raise ValueError(f"Unsupported execution group: {group_name}")
    return GROUP_UNITS[group_name]


def command_logging_targets(command_name: str) -> tuple[str, ...]:
    if command_name not in COMMAND_LOGGING_TARGETS:
        raise ValueError(f"Unsupported logging command: {command_name}")
    return COMMAND_LOGGING_TARGETS[command_name]
