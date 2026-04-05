BUILD_GROUP = "build"

INSPECT_UNIT = "inspect"
CLEAN_UNIT = "clean"
SELECT_PRODUCTS_UNIT = "select_products"
AGGREGATE_DAILY_UNIT = "aggregate_daily"
FEATURE_ENGINEERING_UNIT = "feature_engineering"
TRAIN_MODEL_UNIT = "train_model"

SIMULATE_COMMAND = "simulate"
EVALUATE_COMMAND = "evaluate"
VALIDATE_COMMAND = "validate"
DASHBOARD_COMMAND = "dashboard"

BUILD_UNITS = (
    INSPECT_UNIT,
    CLEAN_UNIT,
    SELECT_PRODUCTS_UNIT,
    AGGREGATE_DAILY_UNIT,
    FEATURE_ENGINEERING_UNIT,
    TRAIN_MODEL_UNIT,
)

GROUP_UNITS = {
    BUILD_GROUP: BUILD_UNITS,
}

COMMAND_LOGGING_TARGETS = {
    BUILD_GROUP: BUILD_UNITS,
    SIMULATE_COMMAND: (SIMULATE_COMMAND,),
    EVALUATE_COMMAND: (EVALUATE_COMMAND,),
    VALIDATE_COMMAND: (VALIDATE_COMMAND,),
    DASHBOARD_COMMAND: (DASHBOARD_COMMAND,),
}


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
