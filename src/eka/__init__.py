"""Enterprise Knowledge Assistant — an advanced, local-first RAG application.

The package is organised as small, single-responsibility modules:

    config       runtime settings (provider, models, chunking, retrieval)
    providers    LLM + embedding backends (Ollama local / Gemini hosted)
    loaders      read PDF and Markdown/TXT documents from a local folder
    chunking     split documents into overlapping, metadata-rich chunks
    vectorstore  ChromaDB-backed dense vector index
    bm25_index   in-memory BM25 sparse index (keyword retrieval)
    retriever    advanced hybrid retrieval (RRF + multi-query + MMR + rerank)
    memory       multi-turn conversation memory + history-aware condensing
    rag          the end-to-end question -> answer pipeline
    prompts      prompt templates used across the pipeline
"""

__version__ = "1.0.0"
