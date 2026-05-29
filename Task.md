# Task.md — Local Multimodal RAG

## Milestone 0: Project bootstrap
- [x] Создана структура директорий (`app/`, `ingestion/`, `retrieval/`, `models/`, `storage/`, `tests/`, `sample_data/`).
- [x] Добавлены `.env.example`, `requirements.txt`, `Makefile`, `.gitignore`.
- [x] Добавлен базовый Streamlit UI.
- DoD: `streamlit run app/streamlit_app.py` стартует без crash.
- Verification artifact: локальный запуск и UI с секцией upload/chat.

## Milestone 1: Data contracts and storage
- [x] Описаны контракты `IngestionResult`, `VectorRecord`, `ChatAnswer` в Pydantic.
- [x] Реализован `VectorStore` интерфейс.
- [x] Реализованы `LanceDBVectorStore` + fallback `InMemoryVectorStore`.
- [x] Реализован retrieval с фильтрами и `top_k`.
- DoD: вставка/чтение/поиск работают минимум на 3 модальностях.
- Verification artifact: `tests/test_vector_store.py`.

## Milestone 2: Ingestion documents/images
- [x] Реализован ingestion PDF/DOCX/PPTX/XLSX/TXT/MD.
- [x] Реализован fallback extraction для изображений из DOCX/PPTX.
- [x] Реализован chunking и метаданные.
- [x] Реализована image-modality обработка.
- DoD: текст + таблицы + изображения извлекаются и индексируются.
- Verification artifact: `tests/test_pipeline.py`, smoke ingestion.

## Milestone 3: Ingestion audio/video
- [x] Реализовано извлечение аудио из видео через ffmpeg.
- [x] Реализована транскрибация через `mlx-whisper`.
- [x] Транскрипт режется на chunk-и и индексируется.
- DoD: на media-файле появляются chunk-и с привязкой к source/audio uri.
- Verification artifact: `ingestion/media_ingestor.py` + smoke на media-файлах.

## Milestone 4: Captioning and model swap
- [x] Добавлен `LocalModelManager` с режимами `chat`/`vision`.
- [x] Реализован captioning изображений через локальную vision-модель Ollama.
- [x] Caption включается в индекс как семантический текст.
- DoD: для image-assets создаются caption-поля и записи в векторном слое.
- Verification artifact: `models/model_manager.py`, `ingestion/pipeline.py`.

## Milestone 5: Chat orchestration and rendering
- [x] Реализован `ChatService.answer(query, session_state)`.
- [x] Контекст собирается из retrieval результатов.
- [x] В ответе показываются источники и связанные изображения (`st.image`).
- [x] История хранится в `st.session_state.messages`.
- DoD: чат отвечает по индексу и отображает image-uri при наличии.
- Verification artifact: `app/streamlit_app.py`, `app/chat_service.py`.

## Milestone 6: Tests, profiling, stabilization
- [x] Добавлены unit/integration тесты на chunking/store/pipeline/chat.
- [ ] Добавить e2e smoke сценарий с реальными мультимодальными файлами пользователя.
- [ ] Добавить профилирование latency/peak RAM на вашем демо-наборе.
- DoD: проход test-гейта + финальное демо на пользовательском датасете.
- Verification artifact: `pytest` отчет, таблица метрик в AGENTS.MD.

## Inputs needed from user
- [ ] Набор файлов: 1-2 каждого типа (`pdf, docx, pptx, xlsx, png/jpg, mp3/wav, mp4`).
- [ ] Язык данных (`ru/en/mixed`).
- [ ] 5-10 контрольных истин после ingestion документов.
- [ ] 3-5 проверочных фраз из аудио/видео.
- [ ] 15-25 реальных production вопросов для retrieval/chat.
- [ ] Критерии финальной приемки (latency/качество/обязательные модальности).
