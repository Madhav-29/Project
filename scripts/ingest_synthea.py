from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ingestion_service import repository


if __name__ == "__main__":
    count = repository.ingest_synthea()
    print(f"Loaded {count} Synthea patients from data/synthea/csv")
