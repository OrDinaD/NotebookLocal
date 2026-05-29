from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import load_settings
from app.container import build_components
from app.logging_utils import configure_logging


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    store, _, pipeline, retriever = build_components(settings)

    sample = settings.upload_dir / "smoke_sample.txt"
    sample.write_text(
        "Это тестовый документ для smoke ingestion. В нем есть ключевая фраза: яблоко и диаграмма продаж.",
        encoding="utf-8",
    )

    result, indexed = pipeline.ingest_and_index(sample)
    hits = retriever.retrieve("Где упоминается яблоко?", top_k=3)

    print(f"store_count={store.count()}")
    print(f"chunks={len(result.text_chunks)} images={len(result.image_assets)} errors={len(result.errors)}")
    print(f"indexed={len(indexed)} hits={len(hits)}")
    for hit in hits:
        print(f"hit: score={hit.score:.4f} source={hit.source_uri}")


if __name__ == "__main__":
    main()
