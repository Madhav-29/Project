from pathlib import Path

from app.ingestion.local_loader import load_sample_data
from app.timeline.event_builder import build_patient_timeline


def test_timeline_is_chronological():
    data = load_sample_data(Path(__file__).resolve().parents[1])
    timeline = build_patient_timeline(data, "p001")
    dates = [event["date"] for event in timeline if event["date"]]
    assert dates == sorted(dates)
    assert any(event["type"] == "condition" for event in timeline)
