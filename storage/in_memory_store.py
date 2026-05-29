from __future__ import annotations

import math

from models.schemas import RetrievedRecord, VectorRecord
from storage.base import VectorStore


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}

    def upsert(self, records: list[VectorRecord]) -> None:
        for rec in records:
            self._records[rec.id] = rec

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict[str, str] | None = None,
    ) -> list[RetrievedRecord]:
        filters = filters or {}
        hits: list[tuple[float, VectorRecord]] = []
        for rec in self._records.values():
            if any(str(rec.metadata.get(k)) != str(v) for k, v in filters.items()):
                continue
            sim = _cosine_similarity(query_vector, rec.embedding)
            score = (sim + 1.0) / 2.0
            hits.append((score, rec))

        hits.sort(key=lambda item: item[0], reverse=True)
        out: list[RetrievedRecord] = []
        for score, rec in hits[:top_k]:
            out.append(
                RetrievedRecord(
                    id=rec.id,
                    source_uri=rec.source_uri,
                    text=rec.text,
                    score=score,
                    metadata=rec.metadata,
                    image_uri=rec.image_uri,
                )
            )
        return out

    def count(self) -> int:
        return len(self._records)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
