from __future__ import annotations

from app.api.schemas import Gap


def recommended_actions(care_gaps: list[Gap], documentation_gaps: list[Gap], risks: list[Gap]) -> list[str]:
    actions = []
    for gap in care_gaps:
        actions.append(f"Clinician to review: {gap.title}.")
    for gap in documentation_gaps:
        actions.append(f"Validate current-year documentation need: {gap.title}.")
    if risks:
        actions.append("Quality/coding reviewer should validate high-priority risks before operational action.")
    return actions or ["No configured care gaps were detected in the available synthetic evidence."]
