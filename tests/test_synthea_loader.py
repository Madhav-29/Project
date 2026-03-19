from pathlib import Path

from app.ingestion.synthea_loader import has_synthea_data


def test_synthea_detector_handles_empty_directory(tmp_path: Path):
    assert has_synthea_data(tmp_path) is False
