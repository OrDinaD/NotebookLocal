from __future__ import annotations

from models.schemas import RetrievedRecord
from retrieval.embedder import Embedder
from storage.base import VectorStore


class Retriever:
    def __init__(self, store: VectorStore, embedder: Embedder, top_k: int = 5) -> None:
        self.store = store
        self.embedder = embedder
        self.top_k = top_k

    def retrieve(self, query: str, filters: dict[str, str] | None = None, top_k: int | None = None) -> list[RetrievedRecord]:
        k = top_k or self.top_k
        query_vec = self.embedder.embed(query)
        return self.store.search(query_vector=query_vec, top_k=k, filters=filters)
