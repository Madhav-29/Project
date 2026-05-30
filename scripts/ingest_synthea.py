from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

from app.services.ingestion_service import repository


if __name__ == "__main__":
    count = repository.ingest_synthea()
    print(f"Loaded {count} Synthea patients from data/synthea/csv")
