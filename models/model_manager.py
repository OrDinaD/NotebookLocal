from __future__ import annotations

import logging
from pathlib import Path

from models.ollama_client import OllamaClient


logger = logging.getLogger(__name__)


class LocalModelManager:
    def __init__(
        self,
        chat_model: str,
        vision_model: str,
        embed_model: str,
        client: OllamaClient | None = None,
    ) -> None:
        self.chat_model = chat_model
        self.vision_model = vision_model
        self.embed_model = embed_model
        self.client = client or OllamaClient()
        self._mode = "chat"

    @property
    def mode(self) -> str:
        return self._mode

    def switch_to_vision(self) -> None:
        logger.info("Switching to vision mode. Chat model considered inactive.")
        self._mode = "vision"

    def switch_to_chat(self) -> None:
        logger.info("Switching to chat mode. Vision model considered inactive.")
        self._mode = "chat"

    def embed_text(self, text: str) -> list[float]:
        return self.client.embed(self.embed_model, text)

    def caption_images(self, image_paths: list[Path]) -> dict[str, str]:
        self.switch_to_vision()
        captions: dict[str, str] = {}
        for img_path in image_paths:
            try:
                captions[str(img_path)] = self.client.caption_image(self.vision_model, img_path)
            except Exception as exc:  # pragma: no cover - runtime network/model errors
                logger.exception("Failed to caption image %s", img_path)
                captions[str(img_path)] = f"[caption_error] {exc}"
        self.switch_to_chat()
        return captions

    def chat(self, prompt: str, system: str | None = None) -> str:
        return self.client.chat(self.chat_model, prompt=prompt, system=system)
