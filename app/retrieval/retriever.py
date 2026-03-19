from __future__ import annotations

from pathlib import Path

from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider
from app.retrieval.vector_store import LocalJSONVectorStore, VectorStoreBase


class HybridRetriever:
    def __init__(
        self,
        index_path: Path,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStoreBase | None = None,
    ) -> None:
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.store = vector_store or LocalJSONVectorStore(index_path)

    def retrieve(self, question: str, patient_id: str, top_k: int = 6) -> list[dict]:
        query_embedding = self.embedding_provider.embed_texts([question])[0]
        vector_hits = self.store.search(query_embedding, patient_id=patient_id, top_k=top_k)
        query_terms = {term for term in question.lower().split() if len(term) > 2}
        lexical_hits = [
            {
                key: value for key, value in hit.items() if key != "embedding"
            } | {"score": 0.35, "retrieval_match": "keyword"}
            for hit in self.store.records
            if hit.get("patient_id") == patient_id
            and any(
                term in " ".join([
                    hit.get("text", ""),
                    hit.get("source_type", ""),
                    hit.get("description", ""),
                    hit.get("category", ""),
                ]).lower()
                for term in query_terms
            )
        ][:top_k]
        merged = {hit["id"]: hit for hit in lexical_hits}
        for hit in vector_hits:
            merged[hit["id"]] = {**hit, "retrieval_match": hit.get("retrieval_match", "vector")}
        return sorted(merged.values(), key=lambda item: item.get("score", 0), reverse=True)[:top_k]
