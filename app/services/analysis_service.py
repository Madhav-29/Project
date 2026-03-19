from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.api.schemas import AnalyzeResponse, AskResponse, RetrievedContext
from app.rag.evidence_builder import recommended_actions
from app.rag.orchestrator import synthesize, synthesize_with_status
from app.retrieval.chunker import timeline_to_documents
from app.retrieval.embeddings import get_embedding_provider
from app.retrieval.retriever import HybridRetriever
from app.retrieval.vector_store import LocalVectorStore
from app.rules.rule_registry import run_all_rules
from app.services.ingestion_service import PROJECT_ROOT, repository
from app.timeline.event_builder import build_patient_timeline


INDEX_PATH = PROJECT_ROOT / "data" / "vector_index" / "index.json"
ANALYSIS_HISTORY: list[dict] = []


def patient_summary_text(patient: dict) -> str:
    conditions = ", ".join(patient.get("conditions", [])) or "No active conditions in available data"
    return (
        f"{patient.get('name')} (synthetic patient {patient.get('id')}), "
        f"age {patient.get('age') or 'unknown'}, gender {patient.get('gender') or 'unknown'}. "
        f"Known conditions: {conditions}."
    )


def timeline_summary_text(timeline: list[dict]) -> str:
    if not timeline:
        return "No timeline events are available for this patient."
    event_types = sorted({event.get("type", "event") for event in timeline})
    latest = [event for event in timeline if event.get("date")][-5:]
    latest_text = "; ".join(f"{event.get('date')}: {event.get('text')}" for event in latest)
    return (
        f"{len(timeline)} timeline events across {', '.join(event_types)}. "
        f"Recent context: {latest_text or 'No dated events available.'}"
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


def live_overview() -> dict:
    patients = repository.patients()
    indexed = INDEX_PATH.exists()
    return {
        "project": "Clinical AI Platform",
        "status": "live",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": repository.source,
        "patient_count": len(patients),
        "index_ready": indexed,
        "last_analysis": ANALYSIS_HISTORY[-1] if ANALYSIS_HISTORY else None,
        "analysis_count": len(ANALYSIS_HISTORY),
    }


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

    response = AnalyzeResponse(
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
    ANALYSIS_HISTORY.append({
        "patient_id": patient_id,
        "patient_name": patient.get("name"),
        "question": question,
        "care_gaps": len(care_gaps),
        "documentation_gaps": len(documentation_gaps),
        "revenue_quality_risks": len(risks),
        "ran_at": datetime.now(timezone.utc).isoformat(),
    })
    del ANALYSIS_HISTORY[:-25]
    return response


def ask_patient(patient_id: str, question: str) -> AskResponse:
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
    timeline_summary = timeline_summary_text(timeline)
    gaps_payload = {
        "care_gaps": [gap.model_dump() for gap in care_gaps],
        "documentation_gaps": [gap.model_dump() for gap in documentation_gaps],
        "revenue_quality_risks": [gap.model_dump() for gap in risks],
    }
    answer, model_status = synthesize_with_status(
        question=question,
        patient_summary=summary,
        gaps=gaps_payload,
        context=context,
        timeline_events=timeline,
        use_llm=True,
    )
    actions = recommended_actions(care_gaps, documentation_gaps, risks)

    ANALYSIS_HISTORY.append({
        "patient_id": patient_id,
        "patient_name": patient.get("name"),
        "question": question,
        "care_gaps": len(care_gaps),
        "documentation_gaps": len(documentation_gaps),
        "revenue_quality_risks": len(risks),
        "ran_at": datetime.now(timezone.utc).isoformat(),
    })
    del ANALYSIS_HISTORY[:-25]

    return AskResponse(
        patient_id=patient_id,
        question=question,
        answer=answer,
        care_gaps=care_gaps,
        documentation_gaps=documentation_gaps,
        revenue_quality_risks=risks,
        supporting_evidence=[RetrievedContext(**hit) for hit in context],
        recommended_actions=actions,
        timeline_summary=timeline_summary,
        model_status=model_status,  # type: ignore[arg-type]
    )
