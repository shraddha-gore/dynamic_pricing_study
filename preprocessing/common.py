from pathlib import Path
from typing import Iterable

import pandas as pd


def configured_root(project_root: str) -> Path:
    return Path(project_root).resolve()


def configured_path(project_root: str, relative_path: str) -> Path:
    return configured_root(project_root) / relative_path


def configured_path_from_map(project_root: str, path_map: dict[str, str], key: str) -> Path:
    return configured_path(project_root, path_map[key])


def ensure_required_columns(df: pd.DataFrame, required_columns: Iterable[str], context: str) -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for {context}: {missing}")
