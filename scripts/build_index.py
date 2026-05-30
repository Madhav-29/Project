from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

from app.services.analysis_service import build_index


if __name__ == "__main__":
    count = build_index()
    print(f"Indexed {count} patient timeline documents")
