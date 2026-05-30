from __future__ import annotations

from pathlib import Path

from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider
from app.retrieval.vector_store import LocalVectorStore


class HybridRetriever:
    def __init__(self, index_path: Path, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.store = LocalVectorStore(index_path)

    def retrieve(self, question: str, patient_id: str, top_k: int = 6) -> list[dict]:
        query_embedding = self.embedding_provider.embed_texts([question])[0]
        vector_hits = self.store.search(query_embedding, patient_id=patient_id, top_k=top_k)
        lexical_hits = [
            hit for hit in self.store.records
            if hit.get("patient_id") == patient_id and any(term in hit.get("text", "").lower() for term in question.lower().split())
        ][:top_k]
        merged = {hit["id"]: {key: value for key, value in hit.items() if key != "embedding"} for hit in lexical_hits}
        for hit in vector_hits:
            merged[hit["id"]] = hit
        return sorted(merged.values(), key=lambda item: item.get("score", 0), reverse=True)[:top_k]
