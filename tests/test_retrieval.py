from app.services.analysis_service import INDEX_PATH, build_index
from app.retrieval.retriever import HybridRetriever


def test_retrieval_filters_by_patient_and_returns_metadata():
    build_index()
    hits = HybridRetriever(INDEX_PATH).retrieve("diabetes hba1c evidence", patient_id="p001", top_k=5)
    assert hits
    assert all(hit["patient_id"] == "p001" for hit in hits)
    assert {"source_type", "date", "description", "category"}.issubset(hits[0].keys())
