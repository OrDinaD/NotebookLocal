from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from ingestion.document_ingestor import DocumentIngestor
from ingestion.media_ingestor import MediaIngestor
from models.model_manager import LocalModelManager
from models.schemas import IngestionResult, Modality, VectorRecord
from retrieval.embedder import Embedder
from storage.base import VectorStore


logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        doc_ingestor: DocumentIngestor,
        media_ingestor: MediaIngestor,
        embedder: Embedder,
        vector_store: VectorStore,
        model_manager: LocalModelManager,
    ) -> None:
        self.doc_ingestor = doc_ingestor
        self.media_ingestor = media_ingestor
        self.embedder = embedder
        self.vector_store = vector_store
        self.model_manager = model_manager

    def ingest_file(self, source_path: Path) -> IngestionResult:
        ext = source_path.suffix.lower()
        if ext in {".mp4", ".mov", ".mkv", ".avi", ".mp3", ".wav", ".m4a"}:
            return self.media_ingestor.ingest(source_path)
        return self.doc_ingestor.ingest(source_path)

    def caption_images(self, ingestion_result: IngestionResult) -> dict[str, str]:
        image_paths = [Path(img.uri) for img in ingestion_result.image_assets if Path(img.uri).exists()]
        if not image_paths:
            return {}
        return self.model_manager.caption_images(image_paths)

    def embed_and_index(self, ingestion_result: IngestionResult, captions: dict[str, str] | None = None) -> list[VectorRecord]:
        captions = captions or {}
        records: list[VectorRecord] = []

        for chunk in ingestion_result.text_chunks:
            chunk_text = chunk.text
            if not chunk_text.strip():
                continue
            rec = VectorRecord(
                id=str(uuid4()),
                source_uri=ingestion_result.source_uri,
                modality=ingestion_result.modality,
                text=chunk_text,
                caption=None,
                embedding=self.embedder.embed(chunk_text),
                metadata=chunk.metadata,
            )
            records.append(rec)

        for image in ingestion_result.image_assets:
            caption = captions.get(image.uri)
            text_for_embedding = caption or f"Image asset from {ingestion_result.source_uri}: {Path(image.uri).name}"
            rec = VectorRecord(
                id=str(uuid4()),
                source_uri=ingestion_result.source_uri,
                modality=Modality.image,
                text=text_for_embedding,
                caption=caption,
                image_uri=image.uri,
                embedding=self.embedder.embed(text_for_embedding),
                metadata=image.metadata,
            )
            records.append(rec)

        if records:
            self.vector_store.upsert(records)
        return records

    def ingest_and_index(self, source_path: Path) -> tuple[IngestionResult, list[VectorRecord]]:
        result = self.ingest_file(source_path)
        captions = self.caption_images(result)
        indexed = self.embed_and_index(result, captions)
        return result, indexed
