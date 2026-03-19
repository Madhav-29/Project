from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.api.schemas import ReviewEvent
from app.services.ingestion_service import PROJECT_ROOT


AUDIT_PATH = PROJECT_ROOT / "data" / "audit" / "review_events.json"


def _read_events() -> list[dict]:
    if not AUDIT_PATH.exists():
        return []
    return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))


def _write_events(events: list[dict]) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(events, indent=2), encoding="utf-8")


def record_review_event(patient_id: str, gap_id: str, status: str, reviewer: str, note: str) -> ReviewEvent:
    event = ReviewEvent(
        id=f"review_{uuid4().hex[:12]}",
        patient_id=patient_id,
        gap_id=gap_id,
        status=status,  # type: ignore[arg-type]
        reviewer=reviewer,
        note=note,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    events = _read_events()
    events.append(event.model_dump())
    _write_events(events)
    return event


def list_review_events(patient_id: str | None = None) -> list[ReviewEvent]:
    events = _read_events()
    if patient_id:
        events = [event for event in events if event.get("patient_id") == patient_id]
    return [ReviewEvent(**event) for event in events]
