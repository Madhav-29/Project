from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import AnalyzeRequest, AnalyzeResponse, AskRequest, AskResponse, IngestResponse, PatientSummary, ReviewEvent, ReviewRequest
from app.ingestion.synthea_loader import SyntheaDataMissingError
from app.services.analysis_service import analyze_patient, ask_patient, build_index, live_overview
from app.services.audit_service import list_review_events, record_review_event
from app.services.ingestion_service import repository


router = APIRouter()


@router.get(
    "/health",
    tags=["System"],
    summary="Check API health",
    description="Returns service status and the active synthetic data source.",
)
def health() -> dict:
    return {"status": "ok", "project": "Clinical AI Platform", "data_source": repository.source}


@router.get(
    "/live/overview",
    tags=["System"],
    summary="Get assistant runtime overview",
    description="Returns cohort size, evidence-index readiness, data source, and recent analysis metadata.",
)
def live() -> dict:
    return live_overview()


@router.get(
    "/patients",
    response_model=list[PatientSummary],
    tags=["Patients"],
    summary="List synthetic patients",
    description="Returns available synthetic patients with age, gender, and known condition names.",
)
def list_patients() -> list[dict]:
    return repository.patients()


@router.get(
    "/patients/{patient_id}",
    response_model=PatientSummary,
    tags=["Patients"],
    summary="Get synthetic patient context",
    description="Returns demographic and condition context for a synthetic patient.",
)
def get_patient(patient_id: str) -> dict:
    patient = repository.patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post(
    "/ingest/synthea",
    response_model=IngestResponse,
    tags=["Data Operations"],
    summary="Load Synthea CSV data",
    description="Loads Synthea CSV files from `data/synthea/csv`. Falls back to bundled sample data when Synthea files are absent.",
)
def ingest_synthea() -> IngestResponse:
    try:
        count = repository.ingest_synthea()
    except SyntheaDataMissingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestResponse(source="synthea", patients_loaded=count, message="Synthea CSV data loaded.")


@router.post(
    "/index/build",
    tags=["Data Operations"],
    summary="Build local evidence index",
    description="Builds the local vector-style evidence index from patient timeline documents.",
)
def index_build() -> dict:
    count = build_index()
    return {"documents_indexed": count}


@router.post(
    "/analyze-patient",
    response_model=AnalyzeResponse,
    tags=["Analysis"],
    summary="Run structured patient analysis",
    description="Returns structured care gaps, documentation gaps, quality risks, retrieved context, and timeline events.",
)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyze_patient(request.patient_id, request.question, request.use_llm)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/ask",
    response_model=AskResponse,
    tags=["Assistant"],
    summary="Ask the Clinical Gap Intelligence Assistant",
    description=(
        "Primary Swagger workflow. Submit a synthetic patient ID and natural-language clinical question. "
        "The backend automatically retrieves patient evidence, builds timeline context, runs care-gap rules, "
        "performs RAG retrieval, and uses configured OpenAI/Azure OpenAI synthesis when available."
    ),
)
def ask(request: AskRequest) -> AskResponse:
    try:
        return ask_patient(request.patient_id, request.question)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/patients/{patient_id}/reviews",
    response_model=ReviewEvent,
    tags=["Assistant"],
    summary="Record human review for a gap",
    description="Stores a local audit event when a reviewer marks a gap as needs_review, accepted, or dismissed.",
)
def review_gap(patient_id: str, request: ReviewRequest) -> ReviewEvent:
    if not repository.patient(patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")
    return record_review_event(
        patient_id=patient_id,
        gap_id=request.gap_id,
        status=request.status,
        reviewer=request.reviewer,
        note=request.note,
    )


@router.get(
    "/patients/{patient_id}/reviews",
    response_model=list[ReviewEvent],
    tags=["Assistant"],
    summary="List human review audit events",
    description="Returns locally stored review/audit events for the selected synthetic patient.",
)
def patient_reviews(patient_id: str) -> list[ReviewEvent]:
    if not repository.patient(patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")
    return list_review_events(patient_id)
