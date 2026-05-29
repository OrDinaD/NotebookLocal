from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    step = max(1, chunk_size - overlap)
    idx = 0
    while idx < len(cleaned):
        chunk = cleaned[idx : idx + chunk_size]
        if chunk:
            chunks.append(chunk)
        idx += step
    return chunks
