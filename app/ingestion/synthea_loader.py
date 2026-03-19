from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.ingestion.local_loader import REQUIRED_TABLES, load_csv_directory


class SyntheaDataMissingError(FileNotFoundError):
    """Raised when Synthea CSV data is not present."""


def load_synthea_csv(directory: Path) -> dict[str, pd.DataFrame]:
    if not directory.exists():
        raise SyntheaDataMissingError(f"Synthea CSV directory does not exist: {directory}")

    data = load_csv_directory(directory)
    missing = [name for name in REQUIRED_TABLES[:5] if data[name].empty]
    if missing:
        raise SyntheaDataMissingError(
            "Missing required Synthea CSV files: "
            + ", ".join(f"{name}.csv" for name in missing)
            + ". Place generated CSV files in data/synthea/csv or use sample fallback data."
        )
    return data


def has_synthea_data(directory: Path) -> bool:
    return directory.exists() and (directory / "patients.csv").exists()
