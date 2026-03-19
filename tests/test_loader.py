from pathlib import Path

from app.ingestion.local_loader import load_sample_data


def test_sample_loader_reads_patients():
    data = load_sample_data(Path(__file__).resolve().parents[1])
    assert len(data["patients"]) == 5
    assert "conditions" in data
