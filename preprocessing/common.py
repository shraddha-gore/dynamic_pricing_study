from pathlib import Path
from typing import Iterable

import pandas as pd


def configured_root(project_root: str) -> Path:
    return Path(project_root).resolve()


def ensure_required_columns(df: pd.DataFrame, required_columns: Iterable[str], context: str) -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for {context}: {missing}")
