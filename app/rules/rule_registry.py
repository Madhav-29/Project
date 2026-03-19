from __future__ import annotations

from app.api.schemas import Gap
from app.rules.clinical_rules import evaluate_care_gaps, evaluate_documentation_gaps, evaluate_revenue_quality_risks


def run_all_rules(events: list[dict], patient: dict) -> tuple[list[Gap], list[Gap], list[Gap]]:
    care_gaps = evaluate_care_gaps(events, patient)
    documentation_gaps = evaluate_documentation_gaps(events)
    revenue_quality_risks = evaluate_revenue_quality_risks(care_gaps, documentation_gaps)
    return care_gaps, documentation_gaps, revenue_quality_risks
