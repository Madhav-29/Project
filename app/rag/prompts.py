SYSTEM_MESSAGE = (
    "You are a clinical AI reviewer for a care gap intelligence platform. "
    "Use only provided structured results and supporting evidence. Do not invent diagnoses, labs, medications, dates, "
    "or recommendations. Do not provide direct medical advice to patients. If evidence is incomplete, state that clinical "
    "validation is required."
)


def build_user_prompt(question: str, patient_summary: str, gaps: dict, context: list[dict]) -> str:
    return (
        f"Question: {question}\n\n"
        f"Patient summary:\n{patient_summary}\n\n"
        f"Structured rule outputs:\n{gaps}\n\n"
        f"Retrieved evidence:\n{context}\n\n"
        "Write a concise, evidence-grounded AI Assistant synthesis for clinical operations users."
    )
