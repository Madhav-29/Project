from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from app.api.schemas import Evidence, Gap
from app.timeline.temporal_utils import condition_active, documented_in_current_year, latest_by_keyword, latest_encounter_by_keyword, latest_lab_by_name


def _event_date(event: dict[str, Any] | None) -> date | None:
    if not event:
        return None
    parsed = pd.to_datetime(event.get("date"), errors="coerce")
    return None if pd.isna(parsed) else parsed.date()


def _days_since(event: dict[str, Any] | None, today: date) -> int | None:
    event_date = _event_date(event)
    return None if not event_date else (today - event_date).days


def _evidence(event: dict[str, Any] | None, source_type: str = "rule", text: str = "") -> list[Evidence]:
    if event:
        return [Evidence(source_type=event["type"], id=str(event["id"]), date=event.get("date"), text=event.get("text", ""))]
    return [Evidence(source_type=source_type, id="rule", date=None, text=text)]


def _gap(
    title: str,
    reason: str,
    impact: str,
    priority: str,
    time_window: str,
    evidence: list[Evidence],
    gap_type: str = "care_gap",
    confidence: str = "medium",
) -> Gap:
    return Gap(
        type=gap_type,
        title=title,
        reason=reason,
        impact=impact,
        priority=priority,
        confidence=confidence,
        time_window=time_window,
        supporting_evidence=evidence,
    )


def _numeric_value(event: dict[str, Any] | None) -> float | None:
    if not event:
        return None
    raw = event.get("raw", {})
    value = raw.get("VALUE") or raw.get("value")
    try:
        return float(str(value).replace("%", ""))
    except (TypeError, ValueError):
        return None


def evaluate_care_gaps(events: list[dict[str, Any]], patient: dict[str, Any], today: date | None = None) -> list[Gap]:
    today = today or date.today()
    gaps: list[Gap] = []

    has_diabetes = condition_active(events, ["diabetes"])
    has_htn = condition_active(events, ["hypertension", "high blood pressure"])
    has_ckd = condition_active(events, ["chronic kidney disease", "ckd"])
    has_obesity = condition_active(events, ["obesity"]) or any("body mass index" in e.get("text", "").lower() for e in events)
    has_copd = condition_active(events, ["copd", "chronic obstructive pulmonary"])

    if has_diabetes:
        a1c = latest_lab_by_name(events, ["hemoglobin a1c", "hba1c"])
        if a1c is None or (_days_since(a1c, today) or 10_000) > 365:
            gaps.append(_gap(
                "Diabetes HbA1c monitoring due",
                "Active diabetes is present but no HbA1c result was found in the last 12 months.",
                "Quality programs often require ongoing glycemic monitoring for diabetes populations.",
                "high",
                "Last 12 months",
                _evidence(a1c, text="Active diabetes found without recent HbA1c evidence."),
                confidence="high" if a1c else "medium",
            ))
        elif (value := _numeric_value(a1c)) is not None and value >= 8:
            gaps.append(_gap(
                "Diabetes HbA1c appears uncontrolled",
                f"Latest HbA1c is {value:g}, meeting the configured >= 8 threshold.",
                "Elevated HbA1c may indicate a need for clinician review and treatment plan reassessment.",
                "high",
                "Latest HbA1c",
                _evidence(a1c),
                confidence="high",
            ))

        eye_exam = latest_by_keyword(events, "procedure", ["retinal", "eye exam", "ophthalmology"])
        if eye_exam is None or (_days_since(eye_exam, today) or 10_000) > 730:
            gaps.append(_gap(
                "Diabetes retinal exam missing",
                "No retinal or eye exam evidence was found within the configured 24-month lookback.",
                "Missing eye screening can affect preventive diabetes quality performance.",
                "medium",
                "Last 24 months",
                _evidence(eye_exam, text="Active diabetes found without recent retinal exam evidence."),
            ))

    if has_htn:
        bp = latest_lab_by_name(events, ["blood pressure", "systolic", "diastolic"])
        if bp is None or (_days_since(bp, today) or 10_000) > 180:
            gaps.append(_gap(
                "Hypertension BP monitoring due",
                "Active hypertension is present but no recent blood pressure observation was found.",
                "Recent BP evidence supports hypertension management and quality reporting.",
                "high",
                "Last 6 months",
                _evidence(bp, text="Active hypertension found without recent BP evidence."),
            ))

    if has_ckd:
        egfr = latest_lab_by_name(events, ["egfr", "glomerular filtration"])
        if egfr is None or (_days_since(egfr, today) or 10_000) > 365:
            gaps.append(_gap(
                "CKD eGFR monitoring due",
                "Active CKD is present but no eGFR result was found in the last 12 months.",
                "Kidney function monitoring supports CKD staging and risk management.",
                "high",
                "Last 12 months",
                _evidence(egfr, text="Active CKD found without recent eGFR evidence."),
            ))

    if has_obesity:
        bmi_followup = latest_encounter_by_keyword(events, ["nutrition", "weight management", "bmi follow"])
        if bmi_followup is None or (_days_since(bmi_followup, today) or 10_000) > 365:
            gaps.append(_gap(
                "Obesity or BMI follow-up missing",
                "BMI/obesity evidence is present but no weight management follow-up was found in the last year.",
                "Follow-up documentation can support preventive care and risk adjustment context.",
                "medium",
                "Last 12 months",
                _evidence(bmi_followup, text="BMI/obesity evidence found without follow-up encounter."),
            ))

    if has_copd:
        spirometry = latest_by_keyword(events, "procedure", ["spirometry", "pulmonary function"])
        followup = latest_encounter_by_keyword(events, ["copd", "pulmonary"])
        if (spirometry is None or (_days_since(spirometry, today) or 10_000) > 730) and followup is None:
            gaps.append(_gap(
                "COPD follow-up or spirometry missing",
                "COPD is active but recent spirometry or pulmonary follow-up evidence was not found.",
                "Objective pulmonary assessment can support diagnosis validation and care planning.",
                "medium",
                "Last 24 months",
                _evidence(spirometry or followup, text="Active COPD found without recent spirometry or follow-up evidence."),
            ))

    if (patient.get("age") or 0) >= 65:
        wellness = latest_encounter_by_keyword(events, ["annual wellness", "wellness visit"])
        if wellness is None or (_days_since(wellness, today) or 10_000) > 365:
            gaps.append(_gap(
                "Older adult annual wellness visit due",
                "Patient is 65 or older and no annual wellness visit was found in the last 12 months.",
                "Annual wellness visits can surface preventive care, medication, and risk documentation needs.",
                "medium",
                "Last 12 months",
                _evidence(wellness, text="Age >= 65 without recent annual wellness encounter."),
            ))

    med_review = latest_encounter_by_keyword(events, ["medication review", "med reconciliation", "medication reconciliation"])
    if med_review is None or (_days_since(med_review, today) or 10_000) > 365:
        gaps.append(_gap(
            "Medication review due",
            "No medication review or reconciliation encounter was found in the last year.",
            "Medication review lowers safety risk and supports documentation completeness.",
            "medium",
            "Last 12 months",
            _evidence(med_review, text="Medication review not documented in the last year."),
        ))

    return gaps


def evaluate_documentation_gaps(events: list[dict[str, Any]], today: date | None = None) -> list[Gap]:
    today = today or date.today()
    chronic_keywords = ["diabetes", "hypertension", "chronic kidney disease", "ckd", "copd", "obesity"]
    gaps: list[Gap] = []
    for keyword in chronic_keywords:
        if condition_active(events, [keyword]) and not documented_in_current_year(events, [keyword], today):
            gaps.append(_gap(
                "Chronic condition not reassessed this year",
                f"Active {keyword} is present but current-year reassessment documentation was not found.",
                "Annual reassessment supports clinical continuity, coding accuracy, and quality review.",
                "high",
                f"Calendar year {today.year}",
                _evidence(None, text=f"Active {keyword} lacks current-year documentation evidence."),
                gap_type="documentation_gap",
            ))
    return gaps


def evaluate_revenue_quality_risks(care_gaps: list[Gap], documentation_gaps: list[Gap]) -> list[Gap]:
    risks: list[Gap] = []
    for gap in care_gaps + documentation_gaps:
        if gap.priority == "high":
            risks.append(_gap(
                f"Quality or risk-adjustment exposure: {gap.title}",
                gap.reason,
                "May affect measure closure, documentation defensibility, or risk adjustment review. Requires clinical validation.",
                "high",
                gap.time_window,
                gap.supporting_evidence,
                gap_type="revenue_quality_risk",
                confidence=gap.confidence,
            ))
    return risks
