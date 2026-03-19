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
    assert payload["supporting_evidence"]
