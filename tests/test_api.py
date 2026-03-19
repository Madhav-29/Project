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
    assert payload["patient_count"] == 5


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
    assert "patient_summary" in payload
    assert "retrieved_context" in payload
    assert "timeline_events" in payload
    assert payload["audit"]["data_source"] == "synthea"


def test_patient_search_and_index_status():
    search = client.get("/patients/search?q=p001")
    assert search.status_code == 200
    assert search.json()[0]["id"] == "p001"

    all_patients = client.get("/patients")
    assert all_patients.status_code == 200
    assert len(all_patients.json()) == 5

    status = client.get("/index/status")
    assert status.status_code == 200
    assert {"ready", "documents_indexed", "retrieval_strategy", "store_type"}.issubset(status.json().keys())
