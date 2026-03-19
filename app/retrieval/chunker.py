from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> list[str]:
    clean = " ".join(text.split())
    if len(clean) <= chunk_size:
        return [clean] if clean else []
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = start + chunk_size
        chunks.append(clean[start:end])
        start = end - overlap if overlap > 0 else end
        if start <= 0:
            start = end
    return chunks


def timeline_to_documents(patient_id: str, events: list[dict]) -> list[dict]:
    documents: list[dict] = []
    for event in events:
        raw = event.get("raw", {}) or {}
        for idx, chunk in enumerate(chunk_text(event.get("text", ""))):
            documents.append({
                "id": f"{patient_id}:{event.get('type')}:{event.get('id')}:{idx}",
                "patient_id": patient_id,
                "source_type": event.get("type", "timeline"),
                "date": event.get("date"),
                "code": raw.get("CODE") or raw.get("code") or "",
                "description": raw.get("DESCRIPTION") or raw.get("description") or event.get("label", ""),
                "category": event.get("type", "timeline"),
                "text": chunk,
            })
    return documents
