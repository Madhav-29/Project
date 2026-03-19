from __future__ import annotations

from pathlib import Path

from app.api.schemas import AnalyzeResponse, RetrievedContext
from app.rag.evidence_builder import recommended_actions
from app.rag.orchestrator import synthesize
from app.retrieval.chunker import timeline_to_documents
from app.retrieval.embeddings import get_embedding_provider
from app.retrieval.retriever import HybridRetriever
from app.retrieval.vector_store import LocalVectorStore
from app.rules.rule_registry import run_all_rules
from app.services.ingestion_service import PROJECT_ROOT, repository
from app.timeline.event_builder import build_patient_timeline


INDEX_PATH = PROJECT_ROOT / "data" / "vector_index" / "index.json"


def patient_summary_text(patient: dict) -> str:
    conditions = ", ".join(patient.get("conditions", [])) or "No active conditions in available data"
    return (
        f"{patient.get('name')} (synthetic patient {patient.get('id')}), "
        f"age {patient.get('age') or 'unknown'}, gender {patient.get('gender') or 'unknown'}. "
        f"Known conditions: {conditions}."
    )


def build_index() -> int:
    provider = get_embedding_provider()
    documents = []
    for patient in repository.patients():
        timeline = build_patient_timeline(repository.data, patient["id"])
        documents.extend(timeline_to_documents(patient["id"], timeline))
    embeddings = provider.embed_texts([doc["text"] for doc in documents]) if documents else []
    LocalVectorStore(INDEX_PATH).add(documents, embeddings)
    return len(documents)


def analyze_patient(patient_id: str, question: str, use_llm: bool = True) -> AnalyzeResponse:
    patient = repository.patient(patient_id)
    if not patient:
        raise ValueError(f"Unknown patient_id: {patient_id}")

    timeline = build_patient_timeline(repository.data, patient_id)
    if not INDEX_PATH.exists():
        build_index()

    retriever = HybridRetriever(INDEX_PATH)
    context = retriever.retrieve(question, patient_id=patient_id, top_k=8)
    care_gaps, documentation_gaps, risks = run_all_rules(timeline, patient)
    summary = patient_summary_text(patient)
    gaps_payload = {
        "care_gaps": [gap.model_dump() for gap in care_gaps],
        "documentation_gaps": [gap.model_dump() for gap in documentation_gaps],
        "revenue_quality_risks": [gap.model_dump() for gap in risks],
    }
    synthesis = synthesize(question, summary, gaps_payload, context, use_llm=use_llm)

    return AnalyzeResponse(
        patient_id=patient_id,
        patient_summary=summary,
        care_gaps=care_gaps,
        documentation_gaps=documentation_gaps,
        revenue_quality_risks=risks,
        recommended_actions=recommended_actions(care_gaps, documentation_gaps, risks),
        retrieved_context=[RetrievedContext(**hit) for hit in context],
        llm_synthesis=synthesis,
        raw_timeline=timeline,
    )
