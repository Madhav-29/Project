from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Confidence = Literal["high", "medium", "low"]
Priority = Literal["high", "medium", "low"]


class Evidence(BaseModel):
    source_type: str = Field(..., examples=["observation"])
    id: str = Field(..., examples=["p001:observation:Hemoglobin A1c/Hemoglobin.total in Blood:0"])
    date: str | None = None
    text: str = Field(..., examples=["Observation: Hemoglobin A1c/Hemoglobin.total in Blood 8.4 %"])


class Gap(BaseModel):
    type: str = Field(..., examples=["care_gap"])
    title: str = Field(..., examples=["Diabetes HbA1c monitoring due"])
    reason: str = Field(..., examples=["Active diabetes is present but no HbA1c result was found in the last 12 months."])
    impact: str = Field(..., examples=["Quality programs often require ongoing glycemic monitoring for diabetes populations."])
    confidence: Confidence = "medium"
    priority: Priority = "medium"
    time_window: str = Field(..., examples=["Last 12 months"])
    supporting_evidence: list[Evidence] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "patient_id": "p001",
            "question": "Identify care gaps, documentation gaps, and revenue risks",
            "data_source": "synthea",
            "use_llm": True,
        }
    })

    patient_id: str = Field(..., examples=["p001"])
    question: str = Field("Identify care gaps, documentation gaps, and revenue risks", examples=["Identify care gaps, documentation gaps, and revenue risks"])
    data_source: str = "synthea"
    use_llm: bool = Field(True, description="Legacy structured-analysis flag. The `/ask` assistant endpoint uses the configured model automatically.")


class AskRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "patient_id": "p001",
            "question": "What care gaps exist for this patient?",
            "data_source": "synthea",
        }
    })

    patient_id: str = Field(..., examples=["p001"])
    question: str = Field(..., examples=["What care gaps exist for this patient?"])
    data_source: str = Field("synthea", examples=["synthea"])


class ReviewRequest(BaseModel):
    gap_id: str = Field(..., examples=["care_gap:Diabetes HbA1c monitoring due"])
    status: Literal["needs_review", "accepted", "dismissed"]
    reviewer: str = Field("clinical_reviewer", examples=["quality_reviewer"])
    note: str = Field("", examples=["Confirmed for quality team follow-up."])


class ReviewGapRequest(ReviewRequest):
    patient_id: str = Field(..., examples=["p001"])


class ReviewEvent(BaseModel):
    id: str
    patient_id: str
    gap_id: str
    status: Literal["needs_review", "accepted", "dismissed"]
    reviewer: str
    note: str
    timestamp: str


class PatientSummary(BaseModel):
    id: str = Field(..., examples=["p001"])
    name: str = Field(..., examples=["Evelyn Carter"])
    birthdate: str | None = None
    age: int | None = None
    gender: str | None = None
    conditions: list[str] = Field(default_factory=list)


class RetrievedContext(BaseModel):
    id: str = Field(..., examples=["p001:observation:Hemoglobin A1c/Hemoglobin.total in Blood:0"])
    source_type: str = Field(..., examples=["observation"])
    date: str | None = Field(None, examples=["2024-02-10"])
    text: str = Field(..., examples=["Observation: Hemoglobin A1c/Hemoglobin.total in Blood 8.4 %"])
    score: float | None = None


class AuditInfo(BaseModel):
    request_id: str
    timestamp: str
    data_source: str = "synthea"
    retrieval_strategy: str = "hybrid/vector"
    top_k: int = 8
    retrieved_chunks: int = 0
    rules_fired: list[str] = Field(default_factory=list)
    model_status: Literal["enabled", "fallback"]
    latency_ms: int = 0
    model: str | None = None
    confidence: Confidence = "low"
    grounded: bool = False


class AskResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "patient_id": "p001",
            "question": "What care gaps exist for this patient?",
            "answer": "The patient has care gaps related to diabetes monitoring, CKD monitoring, and medication review. Supporting evidence includes active chronic conditions and dated observations from the patient timeline.",
            "patient_summary": "Evelyn Carter (synthetic patient p001), age 65, gender female. Known conditions: Type 2 diabetes.",
            "care_gaps": [],
            "documentation_gaps": [],
            "revenue_quality_risks": [],
            "supporting_evidence": [],
            "retrieved_context": [],
            "timeline_events": [],
            "recommended_actions": ["Clinician to review: Diabetes HbA1c monitoring due."],
            "timeline_summary": "12 timeline events across condition, encounter, medication, observation, and procedure.",
            "model_status": "enabled",
            "audit": {
                "request_id": "req_20260531_000000",
                "timestamp": "2026-05-31T00:00:00+00:00",
                "data_source": "synthea",
                "retrieval_strategy": "hybrid",
                "top_k": 8,
                "retrieved_chunks": 8,
                "model": "gpt-4.1-mini",
                "rules_fired": ["Diabetes HbA1c monitoring due"],
                "model_status": "enabled",
                "confidence": "high",
                "grounded": True,
                "latency_ms": 850,
            },
        }
    })

    patient_id: str
    question: str
    answer: str = Field(..., description="Evidence-grounded assistant answer. Falls back to a clear configuration message when model credentials are unavailable.")
    patient_summary: str
    care_gaps: list[Gap]
    documentation_gaps: list[Gap]
    revenue_quality_risks: list[Gap]
    supporting_evidence: list[RetrievedContext]
    retrieved_context: list[RetrievedContext]
    timeline_events: list[dict[str, Any]] = Field(default_factory=list)
    recommended_actions: list[str]
    timeline_summary: str
    model_status: Literal["enabled", "fallback"]
    audit: AuditInfo


class AnalyzeResponse(BaseModel):
    patient_id: str
    patient_summary: str
    care_gaps: list[Gap]
    documentation_gaps: list[Gap]
    revenue_quality_risks: list[Gap]
    recommended_actions: list[str]
    retrieved_context: list[RetrievedContext]
    llm_synthesis: str
    raw_timeline: list[dict[str, Any]] = Field(default_factory=list)


class IngestResponse(BaseModel):
    source: str = Field(..., examples=["synthea"])
    patients_loaded: int = Field(..., examples=[100])
    message: str = Field(..., examples=["Synthea CSV data loaded."])
