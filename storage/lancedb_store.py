from __future__ import annotations

import logging
from pathlib import Path

from models.schemas import RetrievedRecord, VectorRecord
from storage.base import VectorStore

try:
    import lancedb
except Exception:  # pragma: no cover - optional dep in tests
    lancedb = None


logger = logging.getLogger(__name__)


class LanceDBVectorStore(VectorStore):
    def __init__(self, db_dir: Path, table_name: str = "multimodal_records") -> None:
        if lancedb is None:
            raise RuntimeError("lancedb is not installed")
        self._db = lancedb.connect(str(db_dir))
        self._table_name = table_name
        self._table = self._open_or_create_table()

    def _open_or_create_table(self):
        try:
            return self._db.open_table(self._table_name)
        except Exception:
            return self._db.create_table(
                self._table_name,
                data=[
                    {
                        "id": "bootstrap",
                        "source_uri": "bootstrap://seed",
                        "modality": "text",
                        "text": "seed",
                        "caption": None,
                        "embedding": [0.0, 0.0, 0.0, 0.0],
                        "metadata": {},
                        "image_uri": None,
                    }
                ],
            )

    def upsert(self, records: list[VectorRecord]) -> None:
        payload = [rec.model_dump() for rec in records]
        if not payload:
            return
        self._table.add(payload)

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict[str, str] | None = None,
    ) -> list[RetrievedRecord]:
        q = self._table.search(query_vector)
        out = q.limit(max(top_k * 5, top_k)).to_list()
        records: list[RetrievedRecord] = []
        filters = filters or {}
        for row in out:
            if row.get("id") == "bootstrap":
                continue
            metadata = row.get("metadata") or {}
            if any(str(metadata.get(k)) != str(v) for k, v in filters.items()):
                continue
            dist = float(row.get("_distance", 0.0))
            score = 1.0 / (1.0 + dist)
            records.append(
                RetrievedRecord(
                    id=row["id"],
                    source_uri=row["source_uri"],
                    text=row.get("text", ""),
                    score=score,
                    metadata=metadata,
                    image_uri=row.get("image_uri"),
                )
            )
        return records[:top_k]

    def count(self) -> int:
        # LanceDB API differs by version: prefer count_rows, fallback to table exports.
        try:
            return int(self._table.count_rows("id != 'bootstrap'"))
        except Exception:
            pass

        try:
            return int(self._table.count_rows())
        except Exception:
            pass

        rows: list[dict] = []
        try:
            rows = self._table.to_arrow().to_pylist()
        except Exception:
            try:
                rows = self._table.to_pandas().to_dict(orient="records")
            except Exception:
                logger.exception("Failed to count LanceDB rows")
                return 0

        return sum(1 for row in rows if row.get("id") != "bootstrap")
