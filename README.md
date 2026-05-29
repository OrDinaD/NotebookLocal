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

## Ключевые команды

- `make run` — запуск Streamlit UI.
- `make smoke` — быстрый ingestion smoke test.
- `make test` — unit/integration тесты.
- `make reindex` — переиндексация всех файлов в `sample_data/uploads`.
