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
        for idx, chunk in enumerate(chunk_text(event.get("text", ""))):
            documents.append({
                "id": f"{patient_id}:{event.get('type')}:{event.get('id')}:{idx}",
                "patient_id": patient_id,
                "source_type": event.get("type", "timeline"),
                "date": event.get("date"),
                "text": chunk,
            })
    return documents
