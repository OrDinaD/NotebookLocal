from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import load_settings
from app.container import build_components
from app.logging_utils import configure_logging


ALLOWED_EXT = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".xlsm",
    ".txt",
    ".md",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
    ".mp3",
    ".wav",
    ".m4a",
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
}


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    _, _, pipeline, _ = build_components(settings)

    files = [p for p in settings.upload_dir.rglob("*") if p.is_file() and p.suffix.lower() in ALLOWED_EXT]
    if not files:
        print("No files found for reindex")
        return

    for path in files:
        result, indexed = pipeline.ingest_and_index(path)
        print(
            f"Indexed: {path.name} | chunks={len(result.text_chunks)} images={len(result.image_assets)} "
            f"errors={len(result.errors)} vectors={len(indexed)}"
        )


if __name__ == "__main__":
    main()
