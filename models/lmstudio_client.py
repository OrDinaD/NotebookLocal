from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import requests


class LMStudioClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234",
        api_key: str = "lm-studio",
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def healthcheck(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/v1/models", headers=self._headers(), timeout=5)
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def embed(self, model: str, text: str) -> list[float]:
        payload = {"model": model, "input": text}
        response = requests.post(
            f"{self.base_url}/v1/embeddings",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        data = body.get("data", [])
        if data and isinstance(data, list):
            return data[0].get("embedding", [])
        return []

    def chat(self, model: str, prompt: str, system: str | None = None) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": model, "messages": messages, "temperature": 0.2}
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        choices = body.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")

    def caption_image(self, model: str, image_path: Path, prompt: str | None = None) -> str:
        caption_prompt = prompt or "Опиши изображение подробно на русском: объекты, текст, диаграммы, контекст."
        mime = mimetypes.guess_type(str(image_path))[0] or "image/png"
        encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        image_data_url = f"data:{mime};base64,{encoded}"

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": caption_prompt},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                }
            ],
            "temperature": 0.1,
        }
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        choices = body.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")
