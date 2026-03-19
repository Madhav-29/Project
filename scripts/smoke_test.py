from __future__ import annotations

import argparse

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test the Clinical Gap Intelligence API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    health = requests.get(f"{base_url}/health", timeout=10)
    health.raise_for_status()

    docs = requests.get(f"{base_url}/openapi.json", timeout=10)
    docs.raise_for_status()
    openapi = docs.json()
    assert "/ask" in openapi["paths"], "OpenAPI spec is missing /ask"

    payload = {
        "patient_id": "p001",
        "question": "What care gaps exist for this patient?",
        "data_source": "synthea",
    }
    response = requests.post(f"{base_url}/ask", json=payload, timeout=120)
    response.raise_for_status()
    body = response.json()
    assert body["patient_id"] == "p001"
    assert body["supporting_evidence"], "Expected supporting evidence"
    assert body["audit"]["retrieval_strategy"] == "hybrid"

    print("Smoke test passed")
    print(f"Docs: {base_url}/docs")
    print(f"Model status: {body['model_status']}")
    print(f"Care gaps: {len(body['care_gaps'])}")


if __name__ == "__main__":
    main()
