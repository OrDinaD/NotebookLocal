from __future__ import annotations

from models.model_manager import LocalModelManager
from models.schemas import ChatAnswer, RetrievedRecord
from retrieval.retriever import Retriever


SYSTEM_PROMPT = """Ты локальный мультимодальный ассистент. Отвечай строго по найденному контексту.
Если данных недостаточно, явно скажи об этом. Всегда добавляй ссылки на источники в формате [source_uri]."""


def format_context(records: list[RetrievedRecord]) -> str:
    parts: list[str] = []
    for idx, rec in enumerate(records, start=1):
        parts.append(
            f"[{idx}] source={rec.source_uri} score={rec.score:.4f}\nmetadata={rec.metadata}\ntext={rec.text}"
        )
    return "\n\n".join(parts)


class ChatService:
    def __init__(self, retriever: Retriever, model_manager: LocalModelManager, top_k: int = 5) -> None:
        self.retriever = retriever
        self.model_manager = model_manager
        self.top_k = top_k

    def answer(self, query: str, session_messages: list[dict[str, str]]) -> ChatAnswer:
        records = self.retriever.retrieve(query=query, top_k=self.top_k)
        context = format_context(records)
        history_tail = session_messages[-8:]
        history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history_tail)

        prompt = (
            "История диалога:\n"
            f"{history_text}\n\n"
            "Релевантный контекст:\n"
            f"{context}\n\n"
            "Запрос пользователя:\n"
            f"{query}\n\n"
            "Ответь по-русски."
        )
        text = self.model_manager.chat(prompt=prompt, system=SYSTEM_PROMPT)
        image_uris = [r.image_uri for r in records if r.image_uri]
        return ChatAnswer(text=text, cited_records=records, image_uris=[u for u in image_uris if u])
