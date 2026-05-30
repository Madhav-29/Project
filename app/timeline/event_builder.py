from __future__ import annotations

from typing import Any

from app.ingestion.normalization import first_present, parse_date, rows_for_patient


def _event(
    event_type: str,
    source_id: str,
    date: str | None,
    label: str,
    text: str,
    raw: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": event_type,
        "id": source_id,
        "date": date,
        "label": label,
        "text": text,
        "raw": raw,
    }


def build_patient_timeline(data: dict[str, Any], patient_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    for row in rows_for_patient(data.get("conditions"), patient_id):
        label = first_present(row, "DESCRIPTION", "CODE", "description")
        start = parse_date(first_present(row, "START", "start"))
        stop = parse_date(first_present(row, "STOP", "stop"))
        status = "active" if not stop else f"resolved {stop}"
        events.append(_event("condition", first_present(row, "Id", "CODE") or label, start, label, f"Condition: {label} ({status})", row))

    for row in rows_for_patient(data.get("observations"), patient_id):
        label = first_present(row, "DESCRIPTION", "CODE", "description")
        value = first_present(row, "VALUE", "value")
        units = first_present(row, "UNITS", "units")
        date = parse_date(first_present(row, "DATE", "date"))
        events.append(_event("observation", first_present(row, "Id", "CODE") or label, date, label, f"Observation: {label} {value} {units}".strip(), row))

    for row in rows_for_patient(data.get("medications"), patient_id):
        label = first_present(row, "DESCRIPTION", "CODE", "description")
        start = parse_date(first_present(row, "START", "start"))
        stop = parse_date(first_present(row, "STOP", "stop"))
        status = "active" if not stop else f"ended {stop}"
        events.append(_event("medication", first_present(row, "Id", "CODE") or label, start, label, f"Medication: {label} ({status})", row))

    for row in rows_for_patient(data.get("encounters"), patient_id):
        label = first_present(row, "DESCRIPTION", "ENCOUNTERCLASS", "description")
        date = parse_date(first_present(row, "START", "DATE", "date"))
        reason = first_present(row, "REASONDESCRIPTION", "reason")
        text = f"Encounter: {label}. Reason: {reason}".strip()
        events.append(_event("encounter", first_present(row, "Id", "ID") or label, date, label, text, row))

    for row in rows_for_patient(data.get("procedures"), patient_id):
        label = first_present(row, "DESCRIPTION", "CODE", "description")
        date = parse_date(first_present(row, "DATE", "date"))
        events.append(_event("procedure", first_present(row, "Id", "CODE") or label, date, label, f"Procedure: {label}", row))

    for row in rows_for_patient(data.get("careplans"), patient_id):
        label = first_present(row, "DESCRIPTION", "CODE", "description")
        start = parse_date(first_present(row, "START", "start"))
        events.append(_event("careplan", first_present(row, "Id", "CODE") or label, start, label, f"Care plan: {label}", row))

    return sorted(events, key=lambda item: item["date"] or "9999-12-31")
