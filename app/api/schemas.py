from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Confidence = Literal["high", "medium", "low"]
Priority = Literal["high", "medium", "low"]


class Evidence(BaseModel):
    source_type: str
    id: str
    date: str | None = None
    text: str


class Gap(BaseModel):
    type: str
    title: str
    reason: str
    impact: str
    confidence: Confidence = "medium"
    priority: Priority = "medium"
    time_window: str
    supporting_evidence: list[Evidence] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    patient_id: str
    question: str = "Identify care gaps, documentation gaps, and revenue risks"
    data_source: str = "synthea"
    use_llm: bool = True


class AskRequest(BaseModel):
    patient_id: str
    question: str
    data_source: str = "synthea"


class PatientSummary(BaseModel):
    id: str
    name: str
    birthdate: str | None = None
    age: int | None = None
    gender: str | None = None
    conditions: list[str] = Field(default_factory=list)


class RetrievedContext(BaseModel):
    id: str
    source_type: str
    date: str | None = None
    text: str
    score: float | None = None


class AskResponse(BaseModel):
    patient_id: str
    question: str
    answer: str
    care_gaps: list[Gap]
    documentation_gaps: list[Gap]
    revenue_quality_risks: list[Gap]
    supporting_evidence: list[RetrievedContext]
    recommended_actions: list[str]
    timeline_summary: str
    model_status: Literal["enabled", "fallback"]


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
    source: str
    patients_loaded: int
    message: str
