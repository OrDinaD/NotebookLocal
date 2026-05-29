from __future__ import annotations

import hashlib
import html
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


@st.cache_resource(show_spinner=False)
def _get_components():
    return build_components(settings)


store, model_manager, pipeline, retriever = _get_components()
chat_service = ChatService(retriever=retriever, model_manager=model_manager, top_k=settings.top_k)

st.set_page_config(page_title="NotebookLocal", layout="wide")

st.markdown(
    """
<style>
.block-container {padding-top: 0.8rem;}
.small-muted {color: #6b7280; font-size: 0.88rem;}
.src-wrap {margin-top: 8px; display:flex; flex-wrap:wrap; gap:6px;}
.src-chip {
  font-size: 0.78rem;
  padding: 3px 8px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  background: #f8fafc;
  cursor: help;
}
</style>
""",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "ingested_files" not in st.session_state:
    st.session_state.ingested_files = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "processed_upload_hashes" not in st.session_state:
    st.session_state.processed_upload_hashes = set()
if "sources_collapsed" not in st.session_state:
    st.session_state.sources_collapsed = False
if "studio_collapsed" not in st.session_state:
    st.session_state.studio_collapsed = False


def _safe_upload_path(file_name: str, file_hash: str) -> Path:
    path = settings.upload_dir / file_name
    if not path.exists():
        return path
    try:
        existing_hash = hashlib.sha1(path.read_bytes()).hexdigest()
        if existing_hash == file_hash:
            return path
    except Exception:
        pass
    stem = path.stem
    suffix = path.suffix
    return settings.upload_dir / f"{stem}_{file_hash[:8]}{suffix}"


def _ingest_paths(paths: list[Path]) -> list[dict]:
    results: list[dict] = []
    for out_path in paths:
        result, indexed = pipeline.ingest_and_index(out_path)
        row = {
            "path": str(out_path),
            "chunks": len(result.text_chunks),
            "images": len(result.image_assets),
            "errors": [err.message for err in result.errors],
            "indexed": len(indexed),
        }
        st.session_state.ingested_files.append(row)
        results.append(row)
    return results


def _auto_ingest_uploaded(uploaded_files) -> None:
    if not uploaded_files:
        return

    new_paths: list[Path] = []
    for file in uploaded_files:
        payload = file.getvalue()
        file_hash = hashlib.sha1(payload).hexdigest()
        if file_hash in st.session_state.processed_upload_hashes:
            continue
        out_path = _safe_upload_path(file.name, file_hash)
        out_path.write_bytes(payload)
        st.session_state.processed_upload_hashes.add(file_hash)
        new_paths.append(out_path)

    if not new_paths:
        return

    with st.spinner(f"Индексирую {len(new_paths)} файл(ов)..."):
        rows = _ingest_paths(new_paths)

    ok = sum(1 for r in rows if not r["errors"])
    st.toast(f"Добавлено {ok}/{len(rows)} источников")


def _run_query(query: str) -> None:
    if store.count() == 0:
        st.session_state.messages.append({"role": "user", "content": query})
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Пока нет проиндексированных источников. "
                    "Перетащите файл в панель «Источники» и дождитесь завершения индексации."
                ),
                "images": [],
                "citations": [],
            }
        )
        return

    st.session_state.messages.append({"role": "user", "content": query})
    answer = chat_service.answer(query, st.session_state.messages)

    citations = []
    for rec in answer.cited_records:
        snippet = " ".join((rec.text or "").split())[:360]
        citations.append(
            {
                "source_name": Path(rec.source_uri).name,
                "source_uri": rec.source_uri,
                "score": rec.score,
                "snippet": snippet,
            }
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer.text,
            "images": answer.image_uris,
            "citations": citations,
        }
    )


if st.session_state.sources_collapsed and st.session_state.studio_collapsed:
    widths = [0.22, 3.6, 0.22]
elif st.session_state.sources_collapsed:
    widths = [0.22, 2.8, 1.45]
elif st.session_state.studio_collapsed:
    widths = [1.45, 2.8, 0.22]
else:
    widths = [1.45, 2.2, 1.45]

left_col, mid_col, right_col = st.columns(widths)

with left_col:
    if st.session_state.sources_collapsed:
        if st.button("▶ Источники", use_container_width=True):
            st.session_state.sources_collapsed = False
            st.rerun()
    else:
        with st.container(border=True):
            l1, l2 = st.columns([6, 1])
            l1.subheader("Источники")
            if l2.button("◀", help="Свернуть", use_container_width=True):
                st.session_state.sources_collapsed = True
                st.rerun()

            uploaded = st.file_uploader(
                "Добавьте источники (drag & drop)",
                accept_multiple_files=True,
                type=["pdf", "docx", "pptx", "xlsx", "txt", "md", "png", "jpg", "jpeg", "mp3", "wav", "mp4", "mov"],
                key="source_uploader",
            )
            _auto_ingest_uploaded(uploaded)

            if st.button("Добавить демо", use_container_width=True):
                demo = settings.upload_dir / "demo_notebook_source.txt"
                demo.write_text(
                    "Проект: NotebookLocal. Цель: локальный анализ документов и медиа. "
                    "Ключевые функции: ingestion, retrieval, chat, citations, image rendering.",
                    encoding="utf-8",
                )
                _ingest_paths([demo])
                st.toast("Демо-источник добавлен")

            query_sources = st.text_input("Поиск по источникам", "")
            files = st.session_state.ingested_files
            if query_sources.strip():
                files = [row for row in files if query_sources.lower() in Path(row["path"]).name.lower()]

            st.markdown("<div class='small-muted'>Загруженные источники</div>", unsafe_allow_html=True)
            if not files:
                st.info("Пока нет источников")
            for row in files[-30:]:
                name = Path(row["path"]).name
                err = len(row["errors"])
                st.markdown(f"- **{name}** · фрагменты {row['chunks']} · изображения {row['images']} · ошибок {err}")

with mid_col:
    with st.container(border=True):
        st.subheader("Чат")
        q1, q2 = st.columns(2)
        if q1.button("Краткая сводка", use_container_width=True):
            st.session_state.pending_query = "Сделай краткую сводку по загруженным источникам в 5 пунктах"
        if q2.button("Ключевые факты", use_container_width=True):
            st.session_state.pending_query = "Какие ключевые факты есть в загруженных источниках?"

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                citations = message.get("citations", [])
                if citations:
                    chips = []
                    for idx, cite in enumerate(citations, start=1):
                        tip = html.escape(f"{cite['source_name']} | {cite['snippet']}")
                        label = html.escape(cite["source_name"])
                        chips.append(f"<span class='src-chip' title='{tip}'>[{idx}] {label}</span>")
                    st.markdown("<div class='src-wrap'>" + "".join(chips) + "</div>", unsafe_allow_html=True)

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

with right_col:
    if st.session_state.studio_collapsed:
        if st.button("Студия ◀", use_container_width=True):
            st.session_state.studio_collapsed = False
            st.rerun()
    else:
        with st.container(border=True):
            r1, r2 = st.columns([6, 1])
            r1.subheader("Студия")
            if r2.button("▶", help="Свернуть", use_container_width=True):
                st.session_state.studio_collapsed = True
                st.rerun()

            mode_cols_1 = st.columns(2)
            if mode_cols_1[0].button("Аудиопересказ", use_container_width=True):
                st.info("Режим в разработке")
            if mode_cols_1[1].button("Конспект", use_container_width=True):
                st.info("Режим в разработке")

            mode_cols_2 = st.columns(2)
            if mode_cols_2[0].button("Карта ментальная", use_container_width=True):
                st.info("Режим в разработке")
            if mode_cols_2[1].button("Карточки", use_container_width=True):
                st.info("Режим в разработке")

            mode_cols_3 = st.columns(2)
            if mode_cols_3[0].button("Презентация", use_container_width=True):
                st.info("Режим в разработке")
            if mode_cols_3[1].button("Квиз", use_container_width=True):
                st.info("Режим в разработке")

            st.divider()
            health = "онлайн" if model_manager.healthcheck() else "офлайн"
            st.markdown(f"**Провайдер:** {settings.model_provider}")
            st.markdown(f"**Endpoint:** {settings.model_endpoint}")
            st.markdown(f"**Сервер модели:** {health}")
            st.markdown(f"**Записей в базе:** {store.count()}")
            st.markdown(f"**Модель чата:** {settings.chat_model}")
            st.markdown(f"**Vision-модель:** {settings.vision_model}")

            if st.button("Проверить сервер модели", use_container_width=True):
                if model_manager.healthcheck():
                    st.success("Сервер модели доступен")
                else:
                    st.error("Сервер модели недоступен")

            st.caption("Локальный режим. Без OpenRouter.")

if len(st.session_state.messages) > settings.max_context_messages * 2:
    st.session_state.messages = st.session_state.messages[-settings.max_context_messages * 2 :]
