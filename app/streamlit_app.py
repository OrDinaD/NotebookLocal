from __future__ import annotations

import hashlib
import html
import sys
from datetime import datetime
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

st.set_page_config(page_title="NotebookLocal", layout="wide")


@st.cache_resource(show_spinner=False)
def _get_components():
    return build_components(settings)


store, model_manager, pipeline, retriever = _get_components()
chat_service = ChatService(retriever=retriever, model_manager=model_manager, top_k=settings.top_k)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  --bg-main: #eef2f6;
  --bg-shell: #e5eaf1;
  --bg-card: #f7f9fc;
  --bg-soft: #edf2f8;
  --text-main: #2f3442;
  --text-muted: #6f7788;
  --line: #cfd7e4;
  --accent: #ff5d52;
  --accent-soft: #ffe1dd;
  --radius-lg: 20px;
  --radius-md: 14px;
}

html, body, [class*="css"] {
  font-family: "Manrope", "Segoe UI", sans-serif;
}

[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1200px 500px at -5% -10%, #f5f8fd 0%, transparent 60%),
    radial-gradient(900px 420px at 105% 0%, #f3f6fb 0%, transparent 55%),
    var(--bg-main);
}

[data-testid="stHeader"] {
  background: rgba(238, 242, 246, 0.72);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #dde3ec;
}

.stAppDeployButton,
[data-testid="stToolbar"],
[data-testid="stDecoration"] {
  display: none !important;
}

.main .block-container {
  padding-top: 3.35rem;
  padding-bottom: 1.25rem;
  max-width: 1760px;
}

.workspace-shell {
  background: var(--bg-shell);
  border: 1px solid #d6ddea;
  border-radius: 26px;
  padding: 14px;
  box-shadow: 0 16px 40px rgba(27, 37, 56, 0.08);
}

[data-testid="stHorizontalBlock"] > div {
  transition: all 260ms cubic-bezier(0.2, 0.7, 0.2, 1);
}

[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: var(--radius-lg) !important;
  border-color: var(--line) !important;
  background: var(--bg-card);
}

.stSubheader {
  color: var(--text-main);
  font-weight: 800;
}

.small-muted {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.upload-note {
  color: var(--text-muted);
  font-size: 0.92rem;
  margin-top: 0.1rem;
  margin-bottom: 0.55rem;
}

.src-wrap {
  margin-top: 9px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.src-chip {
  font-size: 0.78rem;
  padding: 4px 9px;
  border-radius: 999px;
  border: 1px solid #d2d9e5;
  background: #f8fbff;
  color: #334055;
  cursor: help;
  transition: transform 120ms ease, border-color 120ms ease;
}

.src-chip:hover {
  transform: translateY(-1px);
  border-color: #b6c2d3;
}

.st-key-studio-output {
  background: var(--bg-soft);
  border-radius: var(--radius-md);
  border: 1px dashed #cdd8e8;
  padding: 2px;
}

.studio-line {
  padding: 9px 11px;
  border-radius: 10px;
  border: 1px solid #d7e0ed;
  background: #f9fcff;
  margin-bottom: 8px;
}

.studio-mode button {
  border-radius: 12px !important;
}

.st-key-source-search input,
.st-key-chat-input textarea,
.stChatInputContainer textarea {
  background: #f4f7fb !important;
}

[data-testid="stFileUploaderDropzone"] {
  background: #f0f4fa;
  border: 1px dashed #c8d2df;
  border-radius: 14px;
}

[data-testid="stFileUploaderDropzone"]:hover {
  border-color: #9fb2c9;
  background: #eef3f9;
}

.stButton > button {
  border-radius: 12px;
}

.stButton > button[kind="primary"] {
  background: linear-gradient(180deg, #ff6e63, #ef564a);
  border: 0;
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
if "studio_outputs" not in st.session_state:
    st.session_state.studio_outputs = []


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

    ok = sum(1 for row in rows if not row["errors"])
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


def _push_studio_output(mode_name: str) -> None:
    st.session_state.studio_outputs.append(
        {
            "mode": mode_name,
            "time": datetime.now().strftime("%H:%M:%S"),
            "status": "Режим пока в разработке. Здесь появится результат генерации по выбранному режиму.",
        }
    )


if st.session_state.sources_collapsed and st.session_state.studio_collapsed:
    widths = [0.35, 4.2, 0.35]
elif st.session_state.sources_collapsed:
    widths = [0.35, 2.75, 1.75]
elif st.session_state.studio_collapsed:
    widths = [1.75, 2.75, 0.35]
else:
    widths = [1.75, 2.5, 1.75]

st.markdown("<div class='workspace-shell'>", unsafe_allow_html=True)
left_col, mid_col, right_col = st.columns(widths, gap="medium")

with left_col:
    if st.session_state.sources_collapsed:
        with st.container(border=True):
            if st.button("▶", key="expand_left_panel", help="Развернуть источники", use_container_width=True):
                st.session_state.sources_collapsed = False
                st.rerun()
    else:
        with st.container(border=True):
            header_l, header_r = st.columns([7, 1])
            header_l.subheader("Источники")
            if header_r.button("◀", key="collapse_left_panel", help="Свернуть", use_container_width=True):
                st.session_state.sources_collapsed = True
                st.rerun()

            st.caption("Добавьте источники (drag & drop)")
            uploaded = st.file_uploader(
                "Загрузка источников",
                accept_multiple_files=True,
                type=["pdf", "docx", "pptx", "xlsx", "txt", "md", "png", "jpg", "jpeg", "mp3", "wav", "mp4", "mov"],
                key="source_uploader",
                label_visibility="collapsed",
            )
            _auto_ingest_uploaded(uploaded)
            st.markdown(
                "<div class='upload-note'>200MB per file • PDF, DOCX, PPTX, XLSX, TXT, MD, PNG, JPG, MP3, WAV, MP4</div>",
                unsafe_allow_html=True,
            )

            if st.button("Добавить демо", use_container_width=True):
                demo = settings.upload_dir / "demo_notebook_source.txt"
                demo.write_text(
                    "Проект: NotebookLocal. Цель: локальный анализ документов и медиа. "
                    "Ключевые функции: ingestion, retrieval, chat, citations, image rendering.",
                    encoding="utf-8",
                )
                _ingest_paths([demo])
                st.toast("Демо-источник добавлен")

            query_sources = st.text_input("Поиск по источникам", "", key="source-search")
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

        quick_a, quick_b = st.columns(2)
        if quick_a.button("Краткая сводка", use_container_width=True):
            st.session_state.pending_query = "Сделай краткую сводку по загруженным источникам в 5 пунктах"
        if quick_b.button("Ключевые факты", use_container_width=True):
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
        with st.container(border=True):
            if st.button("▶", key="expand_right_panel", help="Развернуть студию", use_container_width=True):
                st.session_state.studio_collapsed = False
                st.rerun()
    else:
        with st.container(border=True):
            header_l, header_r = st.columns([7, 1])
            header_l.subheader("Студия")
            if header_r.button("▶", key="collapse_right_panel", help="Свернуть", use_container_width=True):
                st.session_state.studio_collapsed = True
                st.rerun()

            mode_grid = [
                ("Аудиопересказ", "Конспект"),
                ("Карта ментальная", "Карточки"),
                ("Презентация", "Квиз"),
            ]
            for left_mode, right_mode in mode_grid:
                c1, c2 = st.columns(2)
                if c1.button(left_mode, use_container_width=True, key=f"mode_{left_mode}"):
                    _push_studio_output(left_mode)
                if c2.button(right_mode, use_container_width=True, key=f"mode_{right_mode}"):
                    _push_studio_output(right_mode)

            st.markdown("##### Вывод студии")
            with st.container(border=True, key="studio-output", height=210):
                outputs = st.session_state.studio_outputs
                if not outputs:
                    st.info("Здесь будут появляться результаты режимов: аудио, конспект, карта, карточки, презентация, квиз.")
                else:
                    for item in outputs[-6:][::-1]:
                        mode = html.escape(item["mode"])
                        status = html.escape(item["status"])
                        when = html.escape(item["time"])
                        st.markdown(
                            f"<div class='studio-line'><b>{mode}</b> · <span class='small-muted'>{when}</span><br>{status}</div>",
                            unsafe_allow_html=True,
                        )

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

st.markdown("</div>", unsafe_allow_html=True)

if len(st.session_state.messages) > settings.max_context_messages * 2:
    st.session_state.messages = st.session_state.messages[-settings.max_context_messages * 2 :]
