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
