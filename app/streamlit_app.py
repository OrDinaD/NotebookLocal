from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.chat_service import ChatService
from app.config import load_settings
from app.container import build_components
from app.logging_utils import configure_logging


settings = load_settings()
configure_logging(settings.log_level)
store, model_manager, pipeline, retriever = build_components(settings)
chat_service = ChatService(retriever=retriever, model_manager=model_manager, top_k=settings.top_k)


st.set_page_config(page_title="Local Multimodal RAG", layout="wide")
st.title("Local Multimodal RAG (Apple Silicon)")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "ingested_files" not in st.session_state:
    st.session_state.ingested_files = []

with st.sidebar:
    st.header("System")
    st.write(f"Store records: **{store.count()}**")
    st.write(f"Model mode: **{model_manager.mode}**")
    st.write(f"Chat model: `{settings.chat_model}`")
    st.write(f"Vision model: `{settings.vision_model}`")

    uploaded = st.file_uploader(
        "Upload files",
        accept_multiple_files=True,
        type=["pdf", "docx", "pptx", "xlsx", "txt", "md", "png", "jpg", "jpeg", "mp3", "wav", "mp4", "mov"],
    )
    if st.button("Ingest uploaded files", type="primary"):
        if not uploaded:
            st.warning("No files selected")
        else:
            for file in uploaded:
                out_path = settings.upload_dir / file.name
                out_path.write_bytes(file.getbuffer())
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
            st.success("Ingestion completed")

    if st.session_state.ingested_files:
        st.subheader("Ingestion log")
        for row in st.session_state.ingested_files[-10:]:
            st.json(row)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

query = st.chat_input("Ask about your local data")
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    answer = chat_service.answer(query, st.session_state.messages)

    response_text = answer.text
    if answer.cited_records:
        response_text += "\n\nSources:\n"
        for rec in answer.cited_records:
            response_text += f"- [{rec.source_uri}] score={rec.score:.4f}\n"

    with st.chat_message("assistant"):
        st.markdown(response_text)
        for image_uri in answer.image_uris:
            image_path = Path(image_uri)
            if image_path.exists():
                st.image(str(image_path), caption=image_path.name)

    st.session_state.messages.append({"role": "assistant", "content": response_text})

if len(st.session_state.messages) > settings.max_context_messages * 2:
    st.session_state.messages = st.session_state.messages[-settings.max_context_messages * 2 :]
