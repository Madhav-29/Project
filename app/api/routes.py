from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import AnalyzeRequest, AnalyzeResponse, AskRequest, IngestResponse, PatientSummary
from app.ingestion.synthea_loader import SyntheaDataMissingError
from app.services.analysis_service import analyze_patient, build_index
from app.services.ingestion_service import repository


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "data_source": repository.source}


@router.get("/patients", response_model=list[PatientSummary])
def list_patients() -> list[dict]:
    return repository.patients()


@router.get("/patients/{patient_id}", response_model=PatientSummary)
def get_patient(patient_id: str) -> dict:
    patient = repository.patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("/ingest/synthea", response_model=IngestResponse)
def ingest_synthea() -> IngestResponse:
    try:
        count = repository.ingest_synthea()
    except SyntheaDataMissingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestResponse(source="synthea", patients_loaded=count, message="Synthea CSV data loaded.")


@router.post("/index/build")
def index_build() -> dict:
    count = build_index()
    return {"documents_indexed": count}


@router.post("/analyze-patient", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyze_patient(request.patient_id, request.question, request.use_llm)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/ask", response_model=AnalyzeResponse)
def ask(request: AskRequest) -> AnalyzeResponse:
    try:
        return analyze_patient(request.patient_id, request.question, request.use_llm)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
