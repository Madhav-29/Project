from __future__ import annotations

from app.llm.base import ChatMessage
from app.llm.router import get_llm_client
from app.rag.prompts import SYSTEM_MESSAGE, build_user_prompt


def synthesize(question: str, patient_summary: str, gaps: dict, context: list[dict], use_llm: bool = True) -> str:
    if not use_llm:
        return "AI-assisted synthesis disabled. Review structured gaps and supporting evidence. Clinical validation required."
    client = get_llm_client()
    prompt = build_user_prompt(question, patient_summary, gaps, context)
    return client.complete([ChatMessage("system", SYSTEM_MESSAGE), ChatMessage("user", prompt)])
