from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Protocol


def cosine(a: list[float], b: list[float]) -> float:
    denom = (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))) or 1.0
    return sum(x * y for x, y in zip(a, b)) / denom


class VectorStoreBase(Protocol):
    records: list[dict[str, Any]]

    def add(self, documents: list[dict[str, Any]], embeddings: list[list[float]]) -> None:
        ...

    def search(self, query_embedding: list[float], patient_id: str | None = None, top_k: int = 5) -> list[dict[str, Any]]:
        ...


class LocalJSONVectorStore:
    """Small local JSON vector store used for deterministic local development."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.records: list[dict[str, Any]] = []
        if path.exists():
            self.records = json.loads(path.read_text(encoding="utf-8"))

    def add(self, documents: list[dict[str, Any]], embeddings: list[list[float]]) -> None:
        self.records = [{**doc, "embedding": embedding} for doc, embedding in zip(documents, embeddings)]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")

    def search(self, query_embedding: list[float], patient_id: str | None = None, top_k: int = 5) -> list[dict[str, Any]]:
        candidates = self.records
        if patient_id:
            candidates = [record for record in candidates if record.get("patient_id") == patient_id]
        scored = []
        for record in candidates:
            score = cosine(query_embedding, record["embedding"])
            scored.append({key: value for key, value in record.items() if key != "embedding"} | {"score": score})
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]


class FaissVectorStore:
    """Production adapter boundary for FAISS-backed retrieval."""

    records: list[dict[str, Any]] = []

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        raise NotImplementedError("FAISS vector store adapter is reserved for production deployment.")


class ChromaVectorStore:
    """Production adapter boundary for Chroma-backed retrieval."""

    records: list[dict[str, Any]] = []

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        raise NotImplementedError("Chroma vector store adapter is reserved for production deployment.")


class AzureAISearchVectorStore:
    """Production adapter boundary for Azure AI Search hybrid/vector retrieval."""

    records: list[dict[str, Any]] = []

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        raise NotImplementedError("Azure AI Search adapter is reserved for production deployment.")


LocalVectorStore = LocalJSONVectorStore
