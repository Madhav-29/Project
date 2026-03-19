SYSTEM_MESSAGE = (
    "You are a clinical AI assistant for clinicians and quality reviewers. Answer only using the provided patient context, "
    "retrieved evidence, timeline events, and rule outputs. Do not invent clinical facts. If evidence is missing, say what "
    "needs validation. Do not provide direct patient-facing medical advice."
)


def build_user_prompt(
    question: str,
    patient_summary: str,
    gaps: dict,
    context: list[dict],
    timeline_events: list[dict] | None = None,
) -> str:
    return (
        f"Question: {question}\n\n"
        f"Patient summary:\n{patient_summary}\n\n"
        f"Structured rule outputs:\n{gaps}\n\n"
        f"Retrieved evidence:\n{context}\n\n"
        f"Timeline events:\n{timeline_events or []}\n\n"
        "Directly answer the user's question. Cite or refer to the supporting evidence snippets where relevant. "
        "Summarize care gaps, documentation gaps, revenue and quality implications, and next review actions for clinicians "
        "or quality teams."
    )
