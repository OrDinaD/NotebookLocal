from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from ingestion.chunking import chunk_text
from models.schemas import IngestionError, IngestionResult, Modality, TextChunk

try:
    import mlx_whisper
except Exception:  # pragma: no cover
    mlx_whisper = None


logger = logging.getLogger(__name__)


class MediaIngestor:
    def __init__(self, whisper_model: str, extract_dir: Path, chunk_size: int = 900, chunk_overlap: int = 150) -> None:
        self.whisper_model = whisper_model
        self.extract_dir = extract_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.extract_dir.mkdir(parents=True, exist_ok=True)

    def ingest(self, source_path: Path) -> IngestionResult:
        ext = source_path.suffix.lower()
        modality = Modality.video if ext in {".mp4", ".mov", ".mkv", ".avi"} else Modality.audio
        result = IngestionResult(source_uri=str(source_path), modality=modality)

        audio_path = source_path
        if modality == Modality.video:
            try:
                audio_path = self._extract_audio(source_path)
            except Exception as exc:
                result.errors.append(IngestionError(code="audio_extract_failed", message=str(exc)))
                return result

        transcript = self._transcribe(audio_path)
        if transcript is None:
            result.errors.append(IngestionError(code="transcribe_failed", message="mlx-whisper failed or unavailable"))
            return result

        result.transcript = transcript
        chunks = chunk_text(transcript, self.chunk_size, self.chunk_overlap)
        for idx, chunk in enumerate(chunks):
            result.text_chunks.append(
                TextChunk(
                    text=chunk,
                    metadata={
                        "chunk_index": idx,
                        "backend": "mlx-whisper",
                        "audio_uri": str(audio_path),
                        "source_uri": str(source_path),
                    },
                )
            )
        return result

    def _extract_audio(self, video_path: Path) -> Path:
        out_dir = self.extract_dir / video_path.stem
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "audio.wav"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(out_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return out_path

    def _transcribe(self, audio_path: Path) -> str | None:
        if mlx_whisper is None:
            logger.warning("mlx-whisper is not available")
            return None
        try:
            result = mlx_whisper.transcribe(str(audio_path), path_or_hf_repo=self.whisper_model)
            return result.get("text", "").strip()
        except Exception as exc:  # pragma: no cover - runtime model failures
            logger.exception("Transcription failed for %s: %s", audio_path, exc)
            return None
