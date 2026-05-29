from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure project root is importable when Streamlit runs this file from app/.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.chat_service import ChatService
from app.config import load_settings
from app.container import build_components
from app.logging_utils import configure_logging


settings = load_settings()
configure_logging(settings.log_level)
store, model_manager, pipeline, retriever = build_components(settings)
chat_service = ChatService(retriever=retriever, model_manager=model_manager, top_k=settings.top_k)

st.set_page_config(page_title="NotebookLite Локальный RAG", layout="wide")

st.markdown(
    """
<style>
.block-container {padding-top: 1rem;}
.panel {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 14px;
  background: #ffffff;
}
.kpi {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px 10px;
  background: #f8fafc;
  margin-bottom: 8px;
}
.small-muted {color: #6b7280; font-size: 0.88rem;}
</style>
""",
    unsafe_allow_html=True,
)

st.title("NotebookLite • Локальный мультимодальный RAG")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "ingested_files" not in st.session_state:
    st.session_state.ingested_files = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None


def _ingest_paths(paths: list[Path]) -> None:
    for out_path in paths:
        result, indexed = pipeline.ingest_and_index(out_path)
        st.session_state.ingested_files.append(
            {
                "path": str(out_path),
                "chunks": len(result.text_chunks),
                "images": len(result.image_assets),
                "errors": [err.message for err in result.errors],
                "indexed": len(indexed),
            }
        )


def _run_query(query: str) -> None:
    if store.count() == 0:
        st.session_state.messages.append({"role": "user", "content": query})
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Пока нет проиндексированных источников. "
                    "Сначала нажмите «Обработать файлы» (или «Добавить демо»), "
                    "а затем повторите запрос."
                ),
                "images": [],
            }
        )
        return

    st.session_state.messages.append({"role": "user", "content": query})
    answer = chat_service.answer(query, st.session_state.messages)

    response_text = answer.text
    if answer.cited_records:
        response_text += "\n\nИсточники:\n"
        for rec in answer.cited_records:
            response_text += f"- [{Path(rec.source_uri).name}] релевантность={rec.score:.4f}\n"

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_text,
            "images": answer.image_uris,
        }
    )


left_col, mid_col, right_col = st.columns([1.1, 2.2, 1.1])

with left_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Источники")
    st.caption("1) Добавьте файлы  2) Нажмите «Обработать файлы»")

    uploaded = st.file_uploader(
        "",
        accept_multiple_files=True,
        type=["pdf", "docx", "pptx", "xlsx", "txt", "md", "png", "jpg", "jpeg", "mp3", "wav", "mp4", "mov"],
        label_visibility="collapsed",
    )

    c1, c2 = st.columns(2)
    with c1:
        ingest_clicked = st.button("Обработать файлы", use_container_width=True, type="primary")
    with c2:
        demo_clicked = st.button("Добавить демо", use_container_width=True)

    if ingest_clicked:
        if not uploaded:
            st.warning("Выберите файлы")
        else:
            paths: list[Path] = []
            for file in uploaded:
                out_path = settings.upload_dir / file.name
                out_path.write_bytes(file.getbuffer())
                paths.append(out_path)
            _ingest_paths(paths)
            st.success("Обработка завершена")

    if demo_clicked:
        demo = settings.upload_dir / "demo_notebook_source.txt"
        demo.write_text(
            "Проект: NotebookLite. Цель: локальный анализ документов и медиа. "
            "Ключевые функции: ingestion, retrieval, chat, citations, image rendering.",
            encoding="utf-8",
        )
        _ingest_paths([demo])
        st.success("Демо-источник добавлен")

    q = st.text_input("Поиск по источникам", "")
    files = st.session_state.ingested_files
    if q.strip():
        files = [row for row in files if q.lower() in Path(row["path"]).name.lower()]

    st.markdown("<div class='small-muted'>Загруженные источники</div>", unsafe_allow_html=True)
    if not files:
        st.info("Пока нет источников")
    for row in files[-25:]:
        name = Path(row["path"]).name
        err = len(row["errors"])
        st.markdown(f"- **{name}** · фрагменты {row['chunks']} · изображения {row['images']} · ошибок {err}")

    st.markdown('</div>', unsafe_allow_html=True)

with mid_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Чат")

    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("Краткая сводка", use_container_width=True):
            st.session_state.pending_query = "Сделай краткую сводку по загруженным источникам в 5 пунктах"
    with q2:
        if st.button("Ключевые факты", use_container_width=True):
            st.session_state.pending_query = "Какие ключевые факты и требования есть в источниках?"
    with q3:
        if st.button("Риски", use_container_width=True):
            st.session_state.pending_query = "Какие риски и пробелы в данных ты видишь?"

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            for image_uri in message.get("images", []):
                p = Path(image_uri)
                if p.exists():
                    st.image(str(p), caption=p.name)

    if st.session_state.pending_query:
        _run_query(st.session_state.pending_query)
        st.session_state.pending_query = None
        st.rerun()

    query = st.chat_input("Спросите по вашим источникам")
    if query:
        _run_query(query)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Студия")

    health = "онлайн" if model_manager.healthcheck() else "офлайн"
    st.markdown(f"<div class='kpi'><b>Провайдер:</b> {settings.model_provider}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi'><b>Endpoint:</b> {settings.model_endpoint}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi'><b>Сервер модели:</b> {health}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi'><b>Записей в базе:</b> {store.count()}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi'><b>Модель чата:</b> {settings.chat_model}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi'><b>Vision-модель:</b> {settings.vision_model}</div>", unsafe_allow_html=True)

    if st.button("Проверить сервер модели", use_container_width=True):
        if model_manager.healthcheck():
            st.success("Сервер модели доступен")
        else:
            st.error("Сервер модели недоступен")

    if st.button("Чеклист первых шагов", use_container_width=True):
        st.info(
            "1) Нажмите «Добавить демо» или загрузите 1–2 файла.\n"
            "2) Нажмите «Обработать файлы».\n"
            "3) Нажмите «Краткая сводка» или задайте свой вопрос."
        )

    st.markdown("<div class='small-muted'>Локальный режим. Без OpenRouter.</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if len(st.session_state.messages) > settings.max_context_messages * 2:
    st.session_state.messages = st.session_state.messages[-settings.max_context_messages * 2 :]
