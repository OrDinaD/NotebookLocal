from __future__ import annotations

import logging
from pathlib import Path

import requests


logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def healthcheck(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def embed(self, model: str, text: str) -> list[float]:
        payload = {"model": model, "input": text}
        response = requests.post(f"{self.base_url}/api/embed", json=payload, timeout=self.timeout)
        if response.status_code == 404:
            fallback = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": model, "prompt": text},
                timeout=self.timeout,
            )
            fallback.raise_for_status()
            return fallback.json().get("embedding", [])
        response.raise_for_status()
        body = response.json()
        embeddings = body.get("embeddings", [])
        if embeddings:
            return embeddings[0]
        return []

    def chat(self, model: str, prompt: str, system: str | None = None) -> str:
        merged = prompt if system is None else f"{system}\n\n{prompt}"
        payload = {"model": model, "prompt": merged, "stream": False}
        response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json().get("response", "")

    def caption_image(self, model: str, image_path: Path, prompt: str | None = None) -> str:
        caption_prompt = prompt or "Опиши изображение подробно на русском: объекты, текст, диаграммы, контекст."
        payload = {
            "model": model,
            "prompt": caption_prompt,
            "images": [str(image_path)],
            "stream": False,
        }
        response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json().get("response", "")
