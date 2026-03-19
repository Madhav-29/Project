from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from time import perf_counter
from uuid import uuid4

from app.api.schemas import AskResponse, RetrievedContext
from app.llm.router import configured_model_name
from app.rag.evidence_builder import recommended_actions
from app.rag.orchestrator import FALLBACK_SUMMARY, synthesize_with_status
from app.retrieval.retriever import HybridRetriever
from app.rules.rule_registry import run_all_rules
from app.services.analysis_service import INDEX_PATH, build_index, patient_summary_text, timeline_summary_text
from app.services.ingestion_service import repository
from app.timeline.event_builder import build_patient_timeline


logger = logging.getLogger(__name__)


@dataclass
class AssistantState:
    request_id: str
    patient_id: str
    question: str
    patient: dict | None = None
    timeline: list[dict] | None = None
    context: list[dict] | None = None
    care_gaps: list | None = None
    documentation_gaps: list | None = None
    risks: list | None = None
    answer: str = FALLBACK_SUMMARY
    model_status: str = "fallback"
    grounded: bool = False


class PatientContextTool:
    def run(self, state: AssistantState) -> AssistantState:
        state.patient = repository.patient(state.patient_id)
        if not state.patient:
            raise ValueError(f"Unknown patient_id: {state.patient_id}")
        return state


class TimelineTool:
    def run(self, state: AssistantState) -> AssistantState:
        state.timeline = build_patient_timeline(repository.data, state.patient_id)
        return state


class RetrieverTool:
    def __init__(self, top_k: int = 8) -> None:
        self.top_k = top_k

    def run(self, state: AssistantState) -> AssistantState:
        if not INDEX_PATH.exists():
            build_index()
        state.context = HybridRetriever(INDEX_PATH).retrieve(state.question, patient_id=state.patient_id, top_k=self.top_k)
        return state


class ClinicalRulesTool:
    def run(self, state: AssistantState) -> AssistantState:
        state.care_gaps, state.documentation_gaps, state.risks = run_all_rules(state.timeline or [], state.patient or {})
        return state


class AnswerGeneratorTool:
    def run(self, state: AssistantState) -> AssistantState:
        gaps_payload = {
            "care_gaps": [gap.model_dump() for gap in state.care_gaps or []],
            "documentation_gaps": [gap.model_dump() for gap in state.documentation_gaps or []],
            "revenue_quality_risks": [gap.model_dump() for gap in state.risks or []],
        }
        state.answer, state.model_status = synthesize_with_status(
            question=state.question,
            patient_summary=patient_summary_text(state.patient or {}),
            gaps=gaps_payload,
            context=state.context or [],
            timeline_events=state.timeline or [],
            use_llm=True,
        )
        return state


class SafetyValidatorTool:
    def run(self, state: AssistantState) -> AssistantState:
        evidence_terms = " ".join(item.get("text", "") for item in state.context or []).lower()
        rule_terms = " ".join(gap.title for gap in (state.care_gaps or []) + (state.documentation_gaps or []) + (state.risks or [])).lower()
        answer = state.answer.lower()
        state.grounded = bool(state.context) and (
            state.model_status == "fallback"
            or any(term in answer for term in ["evidence", "gap", "review", "documentation"])
            or any(token in answer for token in evidence_terms.split()[:20])
            or any(token in answer for token in rule_terms.split()[:20])
        )
        return state


class AuditLoggerTool:
    def run(self, state: AssistantState, started_at: float) -> dict:
        gaps = (state.care_gaps or []) + (state.documentation_gaps or []) + (state.risks or [])
        priorities = [gap.priority for gap in gaps]
        confidence = "high" if "high" in priorities and state.grounded else "medium" if state.grounded else "low"
        return {
            "request_id": state.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_source": "synthea",
            "retrieval_strategy": "hybrid",
            "top_k": 8,
            "retrieved_chunks": len(state.context or []),
            "model": configured_model_name() if state.model_status == "enabled" else "fallback",
            "rules_fired": [gap.title for gap in gaps],
            "model_status": state.model_status,
            "confidence": confidence,
            "grounded": state.grounded,
            "latency_ms": int((perf_counter() - started_at) * 1000),
        }


class ClinicalAssistantOrchestrator:
    def __init__(self) -> None:
        self.patient_tool = PatientContextTool()
        self.timeline_tool = TimelineTool()
        self.retriever_tool = RetrieverTool(top_k=8)
        self.rules_tool = ClinicalRulesTool()
        self.answer_tool = AnswerGeneratorTool()
        self.validator_tool = SafetyValidatorTool()
        self.audit_tool = AuditLoggerTool()

    def run(self, patient_id: str, question: str) -> AskResponse:
        started_at = perf_counter()
        state = AssistantState(request_id=f"req_{uuid4().hex[:12]}", patient_id=patient_id, question=question)
        for tool in [
            self.patient_tool,
            self.timeline_tool,
            self.retriever_tool,
            self.rules_tool,
            self.answer_tool,
            self.validator_tool,
        ]:
            state = tool.run(state)
        audit = self.audit_tool.run(state, started_at)
        actions = recommended_actions(state.care_gaps or [], state.documentation_gaps or [], state.risks or [])
        evidence = [RetrievedContext(**hit) for hit in state.context or []]
        logger.info(
            "assistant_request_completed request_id=%s patient_id=%s retrieved_chunks=%s rules_fired=%s model_status=%s latency_ms=%s",
            audit["request_id"],
            patient_id,
            audit["retrieved_chunks"],
            len(audit["rules_fired"]),
            audit["model_status"],
            audit["latency_ms"],
        )
        return AskResponse(
            patient_id=patient_id,
            question=question,
            answer=state.answer,
            patient_summary=patient_summary_text(state.patient or {}),
            care_gaps=state.care_gaps or [],
            documentation_gaps=state.documentation_gaps or [],
            revenue_quality_risks=state.risks or [],
            supporting_evidence=evidence,
            retrieved_context=evidence,
            timeline_events=state.timeline or [],
            recommended_actions=actions,
            timeline_summary=timeline_summary_text(state.timeline or []),
            model_status=state.model_status,  # type: ignore[arg-type]
            audit=audit,
        )
