# 📚 Enterprise Knowledge Assistant — Advanced RAG

An **Employee Knowledge Assistant** that answers questions about a company's
private documents (HR policies, IT security, travel, benefits, code of conduct,
FAQs) using a **production-oriented Retrieval-Augmented Generation (RAG)**
pipeline.

This is deliberately **more than a basic "chat with PDF"**. It implements
advanced retrieval (hybrid dense + sparse search with rank fusion, multi-query
expansion, LLM re-ranking, and MMR diversification), **multi-turn conversation
memory**, grounded answers with **source citations**, and a clean **Streamlit**
chat interface — all runnable locally.

> **Capstone submission** — GenAI Development Program, Batch 1. Project 2:
> *Enterprise Knowledge Assistant with Advanced RAG*.

---

## ✨ Key Features

| Requirement | Implementation |
|---|---|
| **Document ingestion** | Loads a local folder; supports **PDF** and **Markdown/TXT**; recursive-boundary chunking with overlap. |
| **≥ 2 document formats** | `.pdf` (via `pypdf`) and `.md` / `.txt`. |
| **Embeddings + vector DB** | Embeds each chunk and stores it in a **persistent local ChromaDB**. |
| **Basic retrieval** | Semantic vector search returns the most relevant chunks as context. |
| **Advanced retrieval** | **Hybrid** dense + **BM25** sparse retrieval fused with **Reciprocal Rank Fusion**, plus **multi-query expansion**, **LLM re-ranking**, and **MMR** diversification. |
| **Conversation memory** | Multi-turn memory + **history-aware question condensing** for follow-ups. |
| **Usable interface** | **Streamlit** chat UI with cited sources and a retrieval trace. |
| **Grounded / faithful** | The LLM is instructed to answer **only** from retrieved context and cite sources `[n]`; it declines when the answer isn't in the documents. |
| **Local, no paid infra** | Runs fully on **local Ollama** (open-source). Optionally uses **Gemini** for a hosted live deployment. |

---

## 🏗️ Architecture

```
                 ┌───────────────────────── Ingestion (offline) ─────────────────────────┐
  data/documents │  load (PDF/MD/TXT) → chunk (overlap) → embed → ChromaDB (dense)        │
   (company docs)│                                            └────────→ BM25 (sparse)    │
                 └───────────────────────────────────────────────────────────────────────┘

                 ┌────────────────────────── Query (online) ────────────────────────────┐
   user question │  condense (history-aware)                                             │
        + memory │        │                                                              │
                 │        ▼                                                              │
                 │  multi-query expansion ──► dense search ┐                             │
                 │                          ─► BM25 search ─┼─► RRF fusion ─► LLM rerank  │
                 │                                          ┘        │                    │
                 │                                                   ▼                    │
                 │                                             MMR diversify ─► top-k     │
                 │                                                   │                    │
                 │                            grounded answer ◄──────┘  (cited [n])       │
                 └───────────────────────────────────────────────────────────────────────┘
```

### Why each technique
- **Hybrid (dense + BM25) + RRF** — vector search captures meaning; BM25 catches
  exact terms and acronyms (`PTO`, `VPN`, policy IDs). RRF fuses both rankings
  robustly without score calibration.
- **Multi-query expansion** — the LLM rephrases the question to widen recall.
- **LLM re-ranking** — a single batched LLM call scores the fused candidates for
  relevance, sharpening precision.
- **MMR** — selects a final set that is relevant *and* non-redundant.
- **History-aware condensing** — rewrites "what about for managers?" into a
  standalone query so retrieval works across turns.

---

## 📁 Project Structure

```
enterprise-knowledge-assistant/
├── app.py                     # Streamlit chat UI
├── ingest.py                  # CLI: build the index from data/documents
├── ask.py                     # CLI: ask questions from the terminal
├── requirements.txt
├── .env.example               # configuration template
├── data/documents/            # company documents (sample pack included)
├── scripts/
│   └── generate_sample_docs.py# regenerate the sample company documents
├── samples/
│   ├── sample_questions.md     # example questions
│   └── sample_output.md        # example runs with answers + sources
└── src/eka/                   # the RAG package
    ├── config.py               # settings (provider, models, retrieval)
    ├── providers.py            # Ollama / Gemini backends (one interface)
    ├── loaders.py              # PDF + Markdown/TXT loading
    ├── chunking.py             # recursive-boundary chunker with overlap
    ├── vectorstore.py          # ChromaDB dense vector store
    ├── bm25_index.py           # BM25 sparse index
    ├── retriever.py            # hybrid retrieval: RRF + multi-query + rerank + MMR
    ├── memory.py               # conversation memory + condensing
    ├── indexer.py              # ingestion pipeline
    ├── rag.py                  # end-to-end question → answer pipeline
    └── prompts.py              # prompt templates
```

---

## 🚀 Setup & Run

### Prerequisites
- **Python 3.11+**
- One LLM backend:
  - **Ollama** (default, local, open-source) — install from
    [ollama.com](https://ollama.com), then pull the models:
    ```bash
    ollama pull llama3.2
    ollama pull nomic-embed-text
    ```
  - **or Google Gemini** (hosted) — a free API key from
    [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

### 1. Install
```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env                 # Windows: copy .env.example .env
```
Edit `.env`:
- **Local (open-source):** keep `EKA_PROVIDER=ollama` (nothing else needed).
- **Gemini:** set `EKA_PROVIDER=gemini` and `GOOGLE_API_KEY=...`.

### 3. (Optional) generate the sample documents
A sample pack for the fictional **Aveltra Technologies** is already in
`data/documents/`. To regenerate it:
```bash
python scripts/generate_sample_docs.py
```
To use your own documents, just drop `.pdf` / `.md` / `.txt` files into
`data/documents/`.

### 4. Build the index
```bash
python ingest.py
```
> Switching providers? Re-run `python ingest.py` so the document and query
> embeddings come from the same model.

### 5. Run
**Web UI (recommended):**
```bash
streamlit run app.py
```
**Terminal:**
```bash
python ask.py "How many paid vacation days do I get?"
python ask.py                        # interactive, remembers the conversation
```

---

## ✅ Testing

The suite runs **fully offline** against a deterministic `FakeProvider`
(bag-of-words embeddings + prompt-aware canned responses in
`tests/conftest.py`), so it needs no network, model server, or API key.

```bash
pip install -r requirements-dev.txt
pytest                 # 31 tests: unit, regression (golden-set), performance
pytest -m regression   # just the retrieval-quality guards
```

Coverage: chunking & retrieval math, BM25 + document loaders, conversation
memory, golden-set retrieval regressions, and a latency check.

---

## 🌐 Live Deployment (Streamlit Community Cloud)

The app deploys as a public URL using the **Gemini** backend (a hosted host has
no local Ollama):

1. Push this repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io), create an app from the
   repo with `app.py` as the entry point.
3. In **Settings → Secrets**, add:
   ```toml
   EKA_PROVIDER = "gemini"
   GOOGLE_API_KEY = "your_key_here"
   ```
4. The app builds the index from `data/documents/` on first run.

---

## 🔧 Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `EKA_PROVIDER` | `ollama` | `ollama` (local) or `gemini` (hosted). |
| `OLLAMA_CHAT_MODEL` | `llama3.2` | Local generation model. |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Local embedding model. |
| `GOOGLE_API_KEY` | — | Gemini key (only for `gemini`). |
| `GEMINI_CHAT_MODEL` | `gemini-flash-lite-latest` | Hosted generation model. |
| `GEMINI_EMBED_MODEL` | `gemini-embedding-001` | Hosted embedding model. |
| `EKA_CHUNK_SIZE` / `EKA_CHUNK_OVERLAP` | `900` / `150` | Chunking. |
| `EKA_TOP_K` | `4` | Context chunks passed to the LLM. |
| `EKA_MULTI_QUERY` | `true` | Enable multi-query expansion. |
| `EKA_RERANK` | `true` | Enable LLM re-ranking. |

---

## 🛠️ Tech Stack
**Python · RAG · ChromaDB (vector DB) · BM25 · Reciprocal Rank Fusion · MMR ·
Ollama (llama3.2, nomic-embed-text) · Google Gemini · Streamlit · pypdf**

## 📄 License
MIT — see [LICENSE](LICENSE).
