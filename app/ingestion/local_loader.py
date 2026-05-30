from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_TABLES = (
    "patients",
    "conditions",
    "observations",
    "medications",
    "encounters",
    "procedures",
    "careplans",
)


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str).fillna("")


def load_csv_directory(directory: Path) -> dict[str, pd.DataFrame]:
    return {table: read_csv_if_exists(directory / f"{table}.csv") for table in REQUIRED_TABLES}


def load_sample_data(project_root: Path) -> dict[str, pd.DataFrame]:
    return load_csv_directory(project_root / "data" / "sample")
