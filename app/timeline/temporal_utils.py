from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd


def _date(value: str | None) -> date | None:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def events_within_days(events: list[dict[str, Any]], days: int, today: date | None = None) -> list[dict[str, Any]]:
    today = today or date.today()
    start = today - timedelta(days=days)
    return [event for event in events if (event_date := _date(event.get("date"))) and start <= event_date <= today]


def latest_by_keyword(events: list[dict[str, Any]], event_type: str, keywords: list[str]) -> dict[str, Any] | None:
    lowered = [keyword.lower() for keyword in keywords]
    matches = [
        event for event in events
        if event.get("type") == event_type and any(keyword in event.get("text", "").lower() for keyword in lowered)
    ]
    return matches[-1] if matches else None


def latest_lab_by_name(events: list[dict[str, Any]], names: list[str]) -> dict[str, Any] | None:
    return latest_by_keyword(events, "observation", names)


def latest_encounter_by_keyword(events: list[dict[str, Any]], keywords: list[str]) -> dict[str, Any] | None:
    return latest_by_keyword(events, "encounter", keywords)


def condition_active(events: list[dict[str, Any]], keywords: list[str]) -> bool:
    lowered = [keyword.lower() for keyword in keywords]
    return any(
        event.get("type") == "condition"
        and "resolved" not in event.get("text", "").lower()
        and any(keyword in event.get("text", "").lower() for keyword in lowered)
        for event in events
    )


def documented_in_current_year(events: list[dict[str, Any]], keywords: list[str], today: date | None = None) -> bool:
    today = today or date.today()
    lowered = [keyword.lower() for keyword in keywords]
    for event in events:
        event_date = _date(event.get("date"))
        if event_date and event_date.year == today.year and any(keyword in event.get("text", "").lower() for keyword in lowered):
            return True
    return False
