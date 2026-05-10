"""Thin wrappers over config mappings that expose execution group and logging target metadata."""

from config import COMMAND_LOGGING_TARGETS, GROUP_UNITS


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
