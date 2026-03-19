from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from time import perf_counter

import requests


def score_answer(payload: dict, expected_terms: list[str]) -> dict:
    answer_text = " ".join([
        payload.get("answer", ""),
        " ".join(item.get("text", "") for item in payload.get("supporting_evidence", [])),
    ]).lower()
    matched = [term for term in expected_terms if term.lower() in answer_text]
    return {
        "matched_terms": matched,
        "expected_terms": expected_terms,
        "score": round(len(matched) / max(len(expected_terms), 1), 2),
        "grounded": bool(payload.get("audit", {}).get("grounded")),
        "retrieved_chunks": payload.get("audit", {}).get("retrieved_chunks", 0),
        "model_status": payload.get("model_status"),
    }


def run_eval(base_url: str, questions_path: Path) -> dict:
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    results = []
    for item in questions:
        started = perf_counter()
        response = requests.post(
            f"{base_url.rstrip('/')}/ask",
            json={
                "patient_id": item["patient_id"],
                "question": item["question"],
                "data_source": "synthea",
            },
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        result = score_answer(payload, item.get("expected_evidence_terms", []))
        result.update({
            "patient_id": item["patient_id"],
            "question": item["question"],
            "latency_ms": int((perf_counter() - started) * 1000),
            "request_id": payload.get("audit", {}).get("request_id"),
        })
        results.append(result)
    return {
        "questions": len(results),
        "average_score": round(mean(item["score"] for item in results), 2) if results else 0,
        "grounded_rate": round(mean(1 if item["grounded"] else 0 for item in results), 2) if results else 0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run lightweight Clinical Gap Intelligence RAG evaluation.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--questions", default=str(Path(__file__).with_name("questions.json")))
    args = parser.parse_args()
    summary = run_eval(args.base_url, Path(args.questions))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
