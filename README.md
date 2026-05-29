# NotebookLocal

Локальная мультимодальная RAG-система в стиле NotebookLM:
- загружаете источники (PDF, DOCX, PPTX, XLSX, изображения, аудио/видео)
- система индексирует данные локально
- задаете вопросы и получаете ответ с привязкой к источникам

Проект рассчитан на macOS Apple Silicon и локальные модели (LM Studio / Ollama), без обязательного облака.

## Возможности

- Мультимодальный ingestion:
  - документы: PDF, DOCX, PPTX, XLSX, TXT, MD
  - медиа: PNG/JPG, MP3/WAV, MP4/MOV
- Локальное векторное хранилище на LanceDB
- Локальный чат по источникам с цитированием
- Простая 3-панельная UI (`Источники / Чат / Студия`)
- Fallback-парсинг для стабильной работы на Apple Silicon

## Технологии

- UI: Streamlit
- Хранилище: LanceDB
- Парсинг: pypdf, python-docx, python-pptx, openpyxl, (опционально) Docling
- STT: mlx-whisper
- LLM/VLM/Embeddings: LM Studio (OpenAI-compatible API) или Ollama

## Быстрый старт

```bash
cd /Users/vlad/Desktop/NoteALote
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
make run
```

Открыть: `http://localhost:8501`

## Настройка LM Studio (рекомендуется)

1. Включите `Local Server` в LM Studio (`http://127.0.0.1:1234`).
2. Загрузите модель (например `google/gemma-4-e4b`).
3. Убедитесь, что в `.env`:

```env
RAG_MODEL_PROVIDER=lmstudio
RAG_MODEL_ENDPOINT=http://127.0.0.1:1234
RAG_MODEL_API_KEY=lm-studio
```

## Первый рабочий сценарий

1. Нажмите `Добавить демо` или загрузите свой файл.
2. Нажмите `Обработать файлы`.
3. Дождитесь, пока в `Студии` поле `Записей в базе` станет больше 0.
4. Нажмите `Краткая сводка` или задайте свой вопрос в чат.

## Полезные команды

```bash
make run      # запуск UI
make test     # тесты
make smoke    # smoke ingestion
make reindex  # переиндексация sample_data/uploads
```

## Конфигурация

Основные параметры в `.env`:
- `RAG_MODEL_PROVIDER` (`lmstudio` или `ollama`)
- `RAG_MODEL_ENDPOINT`
- `RAG_CHAT_MODEL`, `RAG_VISION_MODEL`, `RAG_EMBED_MODEL`
- `RAG_WHISPER_MODEL`
- `RAG_USE_DOCLING` (`0` по умолчанию для стабильности)

## Статус и ограничения

- Проект в активной разработке (MVP).
- Для больших PDF возможна длительная индексация.
- Качество ответов зависит от выбранной локальной модели.

## Документация в репозитории

- [AGENTS.MD](./AGENTS.MD) — runbook и операционные детали
- [Task.md](./Task.md) — этапы и чеклист работ
