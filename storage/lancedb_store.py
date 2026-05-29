from __future__ import annotations

import json
import logging
from pathlib import Path

from models.schemas import RetrievedRecord, VectorRecord
from storage.base import VectorStore

try:
    import lancedb
except Exception:  # pragma: no cover - optional dep in tests
    lancedb = None
try:
    import pyarrow as pa
except Exception:  # pragma: no cover
    pa = None


logger = logging.getLogger(__name__)


class LanceDBVectorStore(VectorStore):
    def __init__(self, db_dir: Path, table_name: str = "multimodal_records") -> None:
        if lancedb is None:
            raise RuntimeError("lancedb is not installed")
        if pa is None:
            raise RuntimeError("pyarrow is not installed")
        self._db = lancedb.connect(str(db_dir))
        self._table_name = table_name
        self._table = self._open_or_prepare_table()

    def _open_or_prepare_table(self):
        try:
            table = self._db.open_table(self._table_name)
            if self._is_compatible_schema(table):
                return table
            logger.warning("Incompatible LanceDB schema detected, dropping table %s", self._table_name)
            self._db.drop_table(self._table_name, ignore_missing=True)
            return None
        except Exception:
            return None

    def _create_table(self, embedding_dim: int):
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be > 0")
        schema = pa.schema(
            [
                pa.field("id", pa.string()),
                pa.field("source_uri", pa.string()),
                pa.field("modality", pa.string()),
                pa.field("text", pa.string()),
                pa.field("caption", pa.string()),
                pa.field("embedding", pa.list_(pa.float32(), embedding_dim)),
                pa.field("metadata_json", pa.string()),
                pa.field("image_uri", pa.string()),
            ]
        )
        return self._db.create_table(self._table_name, schema=schema, mode="create")

    def _is_compatible_schema(self, table) -> bool:
        names = list(table.schema.names)
        required = {"id", "source_uri", "modality", "text", "caption", "embedding", "metadata_json", "image_uri"}
        if not required.issubset(set(names)):
            return False
        embedding_field = table.schema.field("embedding")
        return pa.types.is_fixed_size_list(embedding_field.type)

    def _embedding_dim(self) -> int | None:
        if self._table is None:
            return None
        try:
            return int(self._table.schema.field("embedding").type.list_size)
        except Exception:
            return None

    def upsert(self, records: list[VectorRecord]) -> None:
        payload = [
            {
                "id": rec.id,
                "source_uri": rec.source_uri,
                "modality": rec.modality.value if hasattr(rec.modality, "value") else str(rec.modality),
                "text": rec.text,
                "caption": rec.caption,
                "embedding": [float(x) for x in rec.embedding],
                "metadata_json": json.dumps(rec.metadata, ensure_ascii=False),
                "image_uri": rec.image_uri,
            }
            for rec in records
        ]
        if not payload:
            return

        if self._table is None:
            self._table = self._create_table(len(payload[0]["embedding"]))

        expected_dim = self._embedding_dim()
        if expected_dim is not None:
            payload = [row for row in payload if len(row["embedding"]) == expected_dim]
        if not payload:
            logger.warning("All records were skipped due to embedding size mismatch")
            return

        self._table.add(payload)

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict[str, str] | None = None,
    ) -> list[RetrievedRecord]:
        if self._table is None:
            return []
        q = self._table.search(query_vector, vector_column_name="embedding")
        out = q.limit(max(top_k * 5, top_k)).to_list()
        records: list[RetrievedRecord] = []
        filters = filters or {}
        for row in out:
            metadata_raw = row.get("metadata_json") or "{}"
            try:
                metadata = json.loads(metadata_raw)
            except Exception:
                metadata = {}
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
        if self._table is None:
            return 0
        # LanceDB API differs by version: prefer count_rows, fallback to table exports.
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

        return len(rows)
