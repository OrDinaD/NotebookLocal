from __future__ import annotations

from abc import ABC, abstractmethod

from models.schemas import RetrievedRecord, VectorRecord


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, records: list[VectorRecord]) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict[str, str] | None = None,
    ) -> list[RetrievedRecord]:
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError
