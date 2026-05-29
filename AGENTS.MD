# AGENTS.MD — Операционный runbook проекта

## 1. Суть проекта
Система реализует локальный мультимодальный RAG для macOS Apple Silicon (M3 Pro, 18 GB unified memory).
Цель: ingestion + индекс + retrieval + chat по PDF/DOCX/PPTX/XLSX/IMG/AUDIO/VIDEO без облачных LLM.

## 2. Архитектурный стек
- UI: Streamlit (`app/streamlit_app.py`)
- Storage: LanceDB (fallback InMemory) (`storage/`)
- Ingestion: Docling + fallback парсеры (`ingestion/document_ingestor.py`)
- Media ASR: `mlx-whisper` + ffmpeg (`ingestion/media_ingestor.py`)
- LLM/VLM/Embeddings: локально через Ollama (`models/`)
- RAG orchestration: собственная логика на Python (`app/chat_service.py`, `retrieval/`)

## 3. Основные контракты
- `IngestionResult`: нормализованный результат ingestion (chunks/images/tables/errors/transcript).
- `VectorRecord`: единая запись в векторном слое (id, modality, text, caption, embedding, metadata, image_uri).
- `Retriever API`: `retrieve(query, filters, top_k) -> list[RetrievedRecord]`.
- `Chat API`: `answer(query, session_state) -> ChatAnswer`.
- Pipeline jobs: `ingest_file`, `caption_images`, `embed_and_index`, `ingest_and_index`.

## 4. Runtime правила памяти
- Рабочий режим по умолчанию: `chat`.
- На этапе captioning включается `vision` режим (`LocalModelManager.switch_to_vision()`), затем возврат в `chat`.
- Для 18 GB RAM нельзя держать одновременно тяжелую chat LLM и vision LLM в реальном inference-пике.
- Если Ollama или model endpoint недоступен, embedder переключается на hash-эмбеддинг для деградационного режима.

## 5. Переменные окружения
См. `.env.example`:
- `RAG_DB_DIR`, `RAG_UPLOAD_DIR`, `RAG_EXTRACT_DIR`
- `RAG_CHAT_MODEL`, `RAG_VISION_MODEL`, `RAG_EMBED_MODEL`, `RAG_WHISPER_MODEL`
- `RAG_TOP_K`, `RAG_MAX_CONTEXT_MESSAGES`, `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP`

## 6. Локальный запуск
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
make run
```

## 7. Проверка и QA
```bash
make lint
make test
make smoke
```

Обязательный финальный QA на пользовательском наборе:
1. Ingestion всех модальностей без критических ошибок.
2. Корректный retrieval по контрольным вопросам.
3. Визуальный рендер изображений в ответах.
4. Проверка транскрипций на 3-5 референс-фраз.
5. Замер latency и контроль swap/пика RAM.

## 8. Типовые сбои и диагностика
- `lancedb is not installed`:
  - Установить зависимости, либо временно использовать InMemory fallback.
- `ffmpeg not found`:
  - Установить ffmpeg в PATH (`brew install ffmpeg`).
- `mlx-whisper` ошибки модели:
  - Проверить модель в `RAG_WHISPER_MODEL`, проверить доступ/кэш.
- Ollama connection errors:
  - Убедиться, что `ollama serve` запущен, модели подтянуты (`ollama pull ...`).

## 9. Что должен предоставить пользователь
- Демо-набор файлов по всем модальностям.
- Контрольные истины по документам.
- Референс-фразы по аудио/видео.
- Набор production вопросов для финальной оценки.
- Явные критерии приемки.
