from fastapi.testclient import TestClient

import app.rag.orchestrator as orchestrator
from app.api.main import app


client = TestClient(app)


def test_ask_endpoint_returns_audit_contract(monkeypatch):
    monkeypatch.setattr(orchestrator, "has_llm_credentials", lambda: False)
    response = client.post(
        "/ask",
        json={"patient_id": "p001", "question": "What evidence supports these gaps?", "data_source": "synthea"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["audit"]["retrieval_strategy"] == "hybrid"
    assert payload["audit"]["top_k"] == 8
    assert payload["audit"]["retrieved_chunks"] >= 1
    assert payload["audit"]["model_status"] in {"enabled", "fallback"}
    assert payload["supporting_evidence"]


def test_review_gap_endpoint_records_audit_event():
    response = client.post(
        "/review/gap",
        json={
            "patient_id": "p001",
            "gap_id": "care_gap:Diabetes HbA1c monitoring due",
            "status": "needs_review",
            "reviewer": "quality_reviewer",
            "note": "Queued from contract test.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == "p001"
    assert payload["status"] == "needs_review"
