from datetime import date
from pathlib import Path

from app.ingestion.local_loader import load_sample_data
from app.ingestion.normalization import normalize_patient
from app.rules.clinical_rules import evaluate_care_gaps
from app.timeline.event_builder import build_patient_timeline


def test_diabetes_rules_find_gap_or_uncontrolled_a1c():
    data = load_sample_data(Path(__file__).resolve().parents[1])
    patient = normalize_patient(data["patients"].iloc[0].to_dict())
    timeline = build_patient_timeline(data, "p001")
    gaps = evaluate_care_gaps(timeline, patient, today=date(2026, 5, 30))
    titles = {gap.title for gap in gaps}
    assert "Diabetes HbA1c monitoring due" in titles or "Diabetes HbA1c appears uncontrolled" in titles
