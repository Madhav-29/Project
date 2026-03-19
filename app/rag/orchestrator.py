from __future__ import annotations

from app.llm.base import ChatMessage
from app.llm.router import get_llm_client, has_llm_credentials
from app.rag.prompts import SYSTEM_MESSAGE, build_user_prompt


FALLBACK_SUMMARY = "AI Assistant summary unavailable. Configure model credentials to enable generated summaries."


def synthesize_with_status(
    question: str,
    patient_summary: str,
    gaps: dict,
    context: list[dict],
    timeline_events: list[dict] | None = None,
    use_llm: bool = True,
) -> tuple[str, str]:
    if not use_llm:
        return FALLBACK_SUMMARY, "fallback"
    if not has_llm_credentials():
        return FALLBACK_SUMMARY, "fallback"
    client = get_llm_client()
    prompt = build_user_prompt(question, patient_summary, gaps, context, timeline_events)
    try:
        return client.complete([ChatMessage("system", SYSTEM_MESSAGE), ChatMessage("user", prompt)]), "enabled"
    except Exception:
        return FALLBACK_SUMMARY, "fallback"


def synthesize(question: str, patient_summary: str, gaps: dict, context: list[dict], use_llm: bool = True) -> str:
    answer, _ = synthesize_with_status(question, patient_summary, gaps, context, use_llm=use_llm)
    return answer
