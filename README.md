# NoteALote Local Multimodal RAG

Локальная мультимодальная RAG-система для macOS Apple Silicon.

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
make run
```

## LM Studio (рекомендуется)

1. В LM Studio включите `Local Server` на `http://127.0.0.1:1234`.
2. Загрузите chat/vision модель (например `google/gemma-4-e4b`).
3. Проверьте в `.env`:
   - `RAG_MODEL_PROVIDER=lmstudio`
   - `RAG_MODEL_ENDPOINT=http://127.0.0.1:1234`
4. Откройте UI, нажмите `Добавить демо` -> `Обработать файлы` -> `Краткая сводка`.

## Ключевые команды

- `make run` — запуск Streamlit UI.
- `make smoke` — быстрый ingestion smoke test.
- `make test` — unit/integration тесты.
- `make reindex` — переиндексация всех файлов в `sample_data/uploads`.
