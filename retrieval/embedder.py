from __future__ import annotations

import hashlib

from models.model_manager import LocalModelManager


class Embedder:
    def __init__(self, model_manager: LocalModelManager | None = None, dim: int = 384) -> None:
        self.model_manager = model_manager
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        if self.model_manager is not None:
            try:
                vec = self.model_manager.embed_text(text)
                if vec:
                    return vec
            except Exception:
                pass
        return _hash_embedding(text, self.dim)


def _hash_embedding(text: str, dim: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    raw = list(digest) * ((dim // len(digest)) + 1)
    vec = raw[:dim]
    return [((v / 255.0) * 2.0) - 1.0 for v in vec]
