from app.chat_service import ChatService
from models.schemas import RetrievedRecord


class DummyRetriever:
    def retrieve(self, query: str, filters=None, top_k=None):
        return [
            RetrievedRecord(
                id="1",
                source_uri="/tmp/a.txt",
                text="Контекст ответа",
                score=0.9,
                metadata={"page": 1},
                image_uri="/tmp/img.png",
            )
        ]


class DummyModelManager:
    def chat(self, prompt: str, system: str | None = None):
        return "Синтезированный ответ"


def test_chat_answer_contract():
    service = ChatService(retriever=DummyRetriever(), model_manager=DummyModelManager(), top_k=3)
    answer = service.answer("вопрос", [{"role": "user", "content": "вопрос"}])

    assert "Синтезированный" in answer.text
    assert len(answer.cited_records) == 1
    assert answer.image_uris == ["/tmp/img.png"]
