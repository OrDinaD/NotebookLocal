from pathlib import Path

from ingestion.document_ingestor import DocumentIngestor
from ingestion.media_ingestor import MediaIngestor
from ingestion.pipeline import IngestionPipeline
from models.model_manager import LocalModelManager
from retrieval.embedder import Embedder
from storage.in_memory_store import InMemoryVectorStore


class DummyClient:
    def embed(self, model: str, text: str):
        return [0.1, 0.2, 0.3, 0.4]

    def caption_image(self, model: str, image_path: Path):
        return f"caption for {image_path.name}"

    def chat(self, model: str, prompt: str, system: str | None = None):
        return "ok"


def build_pipeline(tmp_path: Path) -> IngestionPipeline:
    manager = LocalModelManager(
        chat_model="chat",
        vision_model="vision",
        embed_model="embed",
        client=DummyClient(),
    )
    embedder = Embedder(model_manager=manager)
    return IngestionPipeline(
        doc_ingestor=DocumentIngestor(extract_dir=tmp_path / "extract"),
        media_ingestor=MediaIngestor(whisper_model="fake", extract_dir=tmp_path / "extract"),
        embedder=embedder,
        vector_store=InMemoryVectorStore(),
        model_manager=manager,
    )


def test_ingest_and_index_text(tmp_path: Path):
    pipeline = build_pipeline(tmp_path)
    src = tmp_path / "doc.txt"
    src.write_text("hello world from test pipeline", encoding="utf-8")

    result, indexed = pipeline.ingest_and_index(src)
    assert len(result.text_chunks) >= 1
    assert not result.errors
    assert len(indexed) >= 1


def test_ingest_image_caption(tmp_path: Path):
    pipeline = build_pipeline(tmp_path)
    img = tmp_path / "image.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")

    result = pipeline.ingest_file(img)
    captions = pipeline.caption_images(result)
    indexed = pipeline.embed_and_index(result, captions)

    assert result.image_assets
    assert captions
    assert any(rec.image_uri for rec in indexed)
