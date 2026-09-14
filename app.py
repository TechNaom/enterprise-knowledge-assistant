"""Streamlit chat UI for the Enterprise Knowledge Assistant.

Run with:
    streamlit run app.py

Features:
* Chat interface with multi-turn conversation memory.
* Grounded answers with expandable, cited source passages.
* A retrieval "trace" so you can see the advanced pipeline working.
* Sidebar controls to (re)build the index and view the active provider.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from eka.config import DATA_DIR, get_settings  # noqa: E402
from eka.indexer import build_index  # noqa: E402
from eka.memory import ConversationMemory  # noqa: E402
from eka.rag import RAGPipeline  # noqa: E402

st.set_page_config(page_title="Enterprise Knowledge Assistant", page_icon="📚", layout="wide")


@st.cache_resource(show_spinner=False)
def load_pipeline() -> RAGPipeline:
    """Build the pipeline once per session (cached across reruns)."""
    return RAGPipeline()


def reset_pipeline() -> None:
    load_pipeline.clear()


# --- Session state ---------------------------------------------------------
if "memory" not in st.session_state:
    st.session_state.memory = ConversationMemory()
if "messages" not in st.session_state:
    st.session_state.messages = []

settings = get_settings()

# --- Sidebar ---------------------------------------------------------------
with st.sidebar:
    st.title("📚 Knowledge Assistant")
    st.caption("Advanced RAG over your company documents")

    st.subheader("Backend")
    st.code(settings.summary(), language="text")

    st.subheader("Knowledge base")
    try:
        pipeline = load_pipeline()
        ready = pipeline.is_ready()
        n_chunks = pipeline.store.count()
    except Exception as exc:  # e.g. provider not reachable
        pipeline, ready, n_chunks = None, False, 0
        st.error(f"Could not start pipeline: {exc}")

    if ready:
        st.success(f"Index ready — {n_chunks} chunks")
    else:
        st.warning("No documents indexed yet.")

    docs = sorted(p.name for p in DATA_DIR.glob("*") if p.is_file()) if DATA_DIR.exists() else []
    with st.expander(f"Documents in data/ ({len(docs)})"):
        for d in docs:
            st.write(f"• {d}")

    if st.button("🔄 Rebuild index from data/documents", use_container_width=True):
        log_area = st.empty()
        logs: list[str] = []

        def _log(msg: str) -> None:
            logs.append(msg)
            log_area.code("\n".join(logs[-12:]), language="text")

        try:
            with st.spinner("Ingesting documents…"):
                build_index(settings=settings, log=_log)
            reset_pipeline()
            st.success("Index rebuilt. Reloading…")
            st.rerun()
        except Exception as exc:
            st.error(f"Ingestion failed: {exc}")

    st.subheader("Retrieval settings")
    st.write(f"Top-k context: **{settings.top_k}**")
    st.write(f"Multi-query: **{'on' if settings.use_multi_query else 'off'}**")
    st.write(f"LLM re-rank: **{'on' if settings.use_rerank else 'off'}**")

    if st.button("🧹 Clear conversation", use_container_width=True):
        st.session_state.memory = ConversationMemory()
        st.session_state.messages = []
        st.rerun()

# --- Main chat area --------------------------------------------------------
st.title("Enterprise Knowledge Assistant")
st.caption(
    "Ask about leave, benefits, IT security, travel, code of conduct and more. "
    "Answers are grounded in company documents and cite their sources."
)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"📎 Sources ({len(msg['sources'])})"):
                for i, s in enumerate(msg["sources"], start=1):
                    st.markdown(f"**[{i}] {s['source']}** · chunk {s['chunk_index']}")
                    st.caption(s["text"][:500] + ("…" if len(s["text"]) > 500 else ""))
        if msg.get("trace"):
            with st.expander("🔍 Retrieval trace"):
                st.json(msg["trace"])

prompt = st.chat_input("Ask a question about company policies…")

if prompt:
    if not pipeline or not ready:
        st.error("Please build the index first (sidebar → Rebuild index).")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                ans = pipeline.answer(prompt, memory=st.session_state.memory)
            st.markdown(ans.text)

            sources = [
                {
                    "source": s.source,
                    "chunk_index": s.chunk_index,
                    "text": s.text,
                }
                for s in ans.sources
            ]
            if sources:
                with st.expander(f"📎 Sources ({len(sources)})"):
                    for i, s in enumerate(sources, start=1):
                        st.markdown(f"**[{i}] {s['source']}** · chunk {s['chunk_index']}")
                        st.caption(s["text"][:500] + ("…" if len(s["text"]) > 500 else ""))

            trace = {
                "standalone_question": ans.standalone_question,
                "expanded_queries": ans.trace.expanded_queries,
                "dense_hits": ans.trace.dense_hits,
                "sparse_hits": ans.trace.sparse_hits,
                "fused_hits": ans.trace.fused_hits,
                "reranked": ans.trace.reranked,
            }
            with st.expander("🔍 Retrieval trace"):
                st.json(trace)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": ans.text,
                "sources": sources,
                "trace": trace,
            }
        )
