from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_patient_response():
    response = client.post("/analyze-patient", json={"patient_id": "p001", "use_llm": False})
    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == "p001"
    assert "care_gaps" in payload
