from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    db_dir: Path
    upload_dir: Path
    extract_dir: Path
    model_provider: str
    model_endpoint: str
    model_api_key: str
    chat_model: str
    vision_model: str
    embed_model: str
    whisper_model: str
    top_k: int
    max_context_messages: int
    chunk_size: int
    chunk_overlap: int
    log_level: str


def load_settings(project_root: Path | None = None) -> Settings:
    load_dotenv()
    root = project_root or Path(__file__).resolve().parents[1]
    data_dir = Path(os.getenv("RAG_DATA_DIR", "./data")).resolve()
    db_dir = Path(os.getenv("RAG_DB_DIR", str(data_dir / "lancedb"))).resolve()
    upload_dir = Path(os.getenv("RAG_UPLOAD_DIR", "./sample_data/uploads")).resolve()
    extract_dir = Path(os.getenv("RAG_EXTRACT_DIR", str(data_dir / "extracted"))).resolve()

    for path in (data_dir, db_dir, upload_dir, extract_dir):
        path.mkdir(parents=True, exist_ok=True)

    return Settings(
        project_root=root,
        data_dir=data_dir,
        db_dir=db_dir,
        upload_dir=upload_dir,
        extract_dir=extract_dir,
        model_provider=os.getenv("RAG_MODEL_PROVIDER", "lmstudio"),
        model_endpoint=os.getenv("RAG_MODEL_ENDPOINT", "http://127.0.0.1:1234"),
        model_api_key=os.getenv("RAG_MODEL_API_KEY", "lm-studio"),
        chat_model=os.getenv("RAG_CHAT_MODEL", "google/gemma-4-e4b"),
        vision_model=os.getenv("RAG_VISION_MODEL", "google/gemma-4-e4b"),
        embed_model=os.getenv("RAG_EMBED_MODEL", "nomic-embed-text"),
        whisper_model=os.getenv("RAG_WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo"),
        top_k=int(os.getenv("RAG_TOP_K", "5")),
        max_context_messages=int(os.getenv("RAG_MAX_CONTEXT_MESSAGES", "10")),
        chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "900")),
        chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "150")),
        log_level=os.getenv("RAG_LOG_LEVEL", "INFO"),
    )
