from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd


def parse_date(value: Any) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def years_old(birthdate: str | None, today: date | None = None) -> int | None:
    if not birthdate:
        return None
    today = today or date.today()
    parsed = pd.to_datetime(birthdate, errors="coerce")
    if pd.isna(parsed):
        return None
    born = parsed.date()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def first_present(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key, "")
        if str(value).strip():
            return str(value)
    return ""


def normalize_patient(row: dict[str, Any]) -> dict[str, Any]:
    first = first_present(row, "FIRST", "first", "first_name")
    last = first_present(row, "LAST", "last", "last_name")
    patient_id = first_present(row, "Id", "ID", "PATIENT", "patient_id")
    birthdate = parse_date(first_present(row, "BIRTHDATE", "birthdate"))
    return {
        "id": patient_id,
        "name": " ".join(part for part in [first, last] if part).strip() or patient_id,
        "birthdate": birthdate,
        "age": years_old(birthdate),
        "gender": first_present(row, "GENDER", "gender"),
    }


def rows_for_patient(df: pd.DataFrame, patient_id: str) -> list[dict[str, Any]]:
    if df.empty:
        return []
    patient_col = "PATIENT" if "PATIENT" in df.columns else "patient_id" if "patient_id" in df.columns else None
    if not patient_col:
        return []
    return df[df[patient_col].astype(str) == str(patient_id)].to_dict("records")
