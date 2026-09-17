# AI_HANDOFF — Enterprise Knowledge Assistant

_Last updated: 2026-09-17_

Read `PROJECT_STATE.md` first for status. This file is orientation for the next
agent (or human) picking the project up.

## Repo map
```
app.py            Streamlit chat UI (deployment entrypoint)
ask.py            CLI: one-shot or interactive Q&A
ingest.py         Build the dense + sparse indices from data/documents/
src/eka/
  config.py       Settings (env-driven): chunk sizes, top_k, provider, etc.
  loaders.py      Markdown + PDF document loading
  chunking.py     Character-window chunking with overlap
  vectorstore.py  ChromaDB wrapper (dense) + Retrieved dataclass
  bm25_index.py   BM25 sparse index (pickled)
  indexer.py      build_index(): orchestrates load → chunk → embed → index
  retriever.py    HybridRetriever: multi-query, RRF, rerank, MMR
  rag.py          RAGPipeline: load-once, ask-many; wires retriever + memory
  memory.py       Conversation memory / query condensing
  providers.py    Ollama (local) + Gemini (hosted) provider adapters
  prompts.py      System/user prompt templates
tests/            Offline suite (see conftest.py FakeProvider) — 31 tests
docs/             PPTX deck + DEMO_SCRIPT.md
storage/          Prebuilt Chroma + BM25 (rebuild with python ingest.py)
```

## How to work on it
- **Tests are offline and fast**: `pip install -r requirements-dev.txt && pytest`.
  No API key or model server needed — `tests/conftest.py` injects a deterministic
  `FakeProvider` via the `provider`/`chroma_dir`/`bm25_path` params on
  `build_index` and `RAGPipeline`. Use that same injection for any new test.
- **Config is env-driven** (`src/eka/config.py`): e.g. `EKA_TOP_K`, `EKA_RERANK`,
  `EKA_MULTI_QUERY`, `EKA_PROVIDER`. Copy `.env.example` → `.env` for local runs.
- **Two providers**: default `ollama` for local dev, `gemini` for the hosted
  Streamlit deployment (`app.py` bridges `st.secrets` → env).

## Gotchas
- BM25 IDF can be 0/negative on tiny corpora; `bm25_index.query` deliberately
  keeps a chunk that literally contains a query term even at zero score.
- The `FakeProvider` reranker is bag-of-words: don't write offline tests that
  assume it can disambiguate meaning (e.g. negation). Semantic-ranking guards
  belong in a live-provider integration test.
- Python 3.14 in the `.venv` here; requirements target 3.11+.

## Next steps if continuing
1. Push to GitHub and (optionally) verify the live Streamlit URL.
2. Possible enhancements: streaming responses, source-document highlighting,
   eval harness with a larger golden set, per-query latency logging.
