from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.ingestion.local_loader import load_sample_data
from app.ingestion.normalization import normalize_patient
from app.ingestion.synthea_loader import SyntheaDataMissingError, has_synthea_data, load_synthea_csv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"
SYNTHEA_DIR = PROJECT_ROOT / "data" / "synthea" / "csv"


class DataRepository:
    def __init__(self) -> None:
        self.source = "sample"
        self.data = self.load_best_available()

    def load_best_available(self) -> dict[str, pd.DataFrame]:
        if has_synthea_data(SYNTHEA_DIR):
            try:
                self.source = "synthea"
                return load_synthea_csv(SYNTHEA_DIR)
            except SyntheaDataMissingError:
                pass
        self.source = "sample"
        return load_sample_data(PROJECT_ROOT)

    def ingest_synthea(self) -> int:
        self.data = load_synthea_csv(SYNTHEA_DIR)
        self.source = "synthea"
        return len(self.data["patients"])

    def patients(self) -> list[dict]:
        if self.data["patients"].empty:
            return []
        patients = [normalize_patient(row) for row in self.data["patients"].to_dict("records")]
        for patient in patients:
            patient["conditions"] = self.condition_names(patient["id"])
        return patients

    def patient(self, patient_id: str) -> dict | None:
        return next((patient for patient in self.patients() if patient["id"] == patient_id), None)

    def condition_names(self, patient_id: str) -> list[str]:
        df = self.data.get("conditions")
        if df is None or df.empty or "PATIENT" not in df.columns:
            return []
        return sorted(set(df[df["PATIENT"].astype(str) == str(patient_id)]["DESCRIPTION"].astype(str).tolist()))


repository = DataRepository()
