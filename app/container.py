from __future__ import annotations

from app.config import Settings
from ingestion.document_ingestor import DocumentIngestor
from ingestion.media_ingestor import MediaIngestor
from ingestion.pipeline import IngestionPipeline
from models.model_manager import LocalModelManager
from retrieval.embedder import Embedder
from retrieval.retriever import Retriever
from storage.in_memory_store import InMemoryVectorStore
from storage.lancedb_store import LanceDBVectorStore


def build_store(settings: Settings):
    try:
        return LanceDBVectorStore(db_dir=settings.db_dir)
    except Exception:
        return InMemoryVectorStore()


def build_components(settings: Settings):
    store = build_store(settings)
    model_manager = LocalModelManager(
        chat_model=settings.chat_model,
        vision_model=settings.vision_model,
        embed_model=settings.embed_model,
    )
    embedder = Embedder(model_manager=model_manager)
    doc_ingestor = DocumentIngestor(
        extract_dir=settings.extract_dir,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    media_ingestor = MediaIngestor(
        whisper_model=settings.whisper_model,
        extract_dir=settings.extract_dir,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    pipeline = IngestionPipeline(
        doc_ingestor=doc_ingestor,
        media_ingestor=media_ingestor,
        embedder=embedder,
        vector_store=store,
        model_manager=model_manager,
    )
    retriever = Retriever(store=store, embedder=embedder, top_k=settings.top_k)
    return store, model_manager, pipeline, retriever
