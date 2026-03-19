from app.services.audit_service import list_review_events, record_review_event


def test_review_event_round_trip(tmp_path, monkeypatch):
    import app.services.audit_service as audit_service

    monkeypatch.setattr(audit_service, "AUDIT_PATH", tmp_path / "review_events.json")
    event = record_review_event(
        patient_id="p001",
        gap_id="care_gap:Diabetes HbA1c monitoring due",
        status="needs_review",
        reviewer="quality_reviewer",
        note="Review during chart prep.",
    )
    events = list_review_events("p001")
    assert events[0].id == event.id
    assert events[0].status == "needs_review"
