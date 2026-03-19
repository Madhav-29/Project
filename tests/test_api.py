from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["project"] == "Clinical AI Platform"


def test_live_overview():
    response = client.get("/live/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["project"] == "Clinical AI Platform"
    assert payload["status"] == "live"


def test_analyze_patient_response():
    response = client.post("/analyze-patient", json={"patient_id": "p001", "use_llm": False})
    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == "p001"
    assert "care_gaps" in payload


def test_ask_response_contract(monkeypatch):
    import app.rag.orchestrator as orchestrator

    monkeypatch.setattr(orchestrator, "has_llm_credentials", lambda: False)
    response = client.post(
        "/ask",
        json={
            "patient_id": "p001",
            "question": "What care gaps exist for this patient?",
            "data_source": "synthea",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == "p001"
    assert payload["question"] == "What care gaps exist for this patient?"
    assert payload["model_status"] in {"enabled", "fallback"}
    assert "answer" in payload
    assert "supporting_evidence" in payload
