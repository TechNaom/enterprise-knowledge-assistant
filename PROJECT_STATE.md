# PROJECT_STATE — Enterprise Knowledge Assistant

_Last updated: 2026-09-17_

## What this is
Capstone project: an **advanced RAG** "Enterprise Knowledge Assistant" that
answers questions over internal company documents (HR, IT, finance policies)
with grounded, cited answers.

## Current status: ✅ Submission-ready

| Area | State |
|------|-------|
| Core RAG pipeline | ✅ Complete — hybrid dense (Chroma) + sparse (BM25), RRF fusion, LLM rerank, MMR diversification, multi-query expansion |
| Conversation memory | ✅ Complete (`src/eka/memory.py`) |
| Providers | ✅ Ollama (local default) + Gemini (hosted, for deployment) |
| Interfaces | ✅ Streamlit chat UI (`app.py`), CLI (`ask.py`), ingestion (`ingest.py`) |
| Sample data | ✅ 6 docs (markdown + PDF) in `data/documents/` |
| Test suite | ✅ **31 passing** — unit, regression (golden-set), performance; fully offline via `FakeProvider` |
| Deployment | ✅ Streamlit-Cloud ready (`st.secrets` → env bridge, auto-build index on first load) |
| Presentation | ✅ `docs/Enterprise_Knowledge_Assistant.pptx` + `docs/DEMO_SCRIPT.md` |

## Architecture (one line)
Query → multi-query expand → dense + BM25 retrieve → RRF fuse → LLM rerank →
MMR diversify → grounded, cited answer, with per-turn conversation memory.

## How to run
```bash
pip install -r requirements.txt          # runtime
pip install -r requirements-dev.txt      # tests (pytest)
python ingest.py                         # build the index
streamlit run app.py                     # web UI   (or)  python ask.py "..."
pytest                                   # 31 tests, offline
```

## Recent work (this session, 2026-09-17)
- Added a full offline test suite (`tests/`) with a deterministic `FakeProvider`.
- Added dependency-injection hooks to `build_index` / `RAGPipeline`
  (`provider`, `chroma_dir`, `bm25_path`) so tests run against isolated storage.
- Fixed a BM25 small-corpus edge case: an exact keyword match with zero IDF was
  being dropped; it is now retained (`src/eka/bm25_index.py`).
- Registered pytest markers (`pytest.ini`), added `requirements-dev.txt`, and a
  Testing section to the README.

## Known limitations / notes
- The offline `FakeProvider` reranker is bag-of-words and cannot disambiguate a
  negated lexical distractor ("sick leave does *not* carry over"). The
  exact-chunk ranking guard is therefore validated only against a live model;
  the offline regression test asserts the softer source-level property. This is
  a test-fixture limitation, not a retriever defect.
- `storage/` (Chroma + BM25 pickle) is committed for demo convenience; rebuild
  anytime with `python ingest.py`.

## Pending before submission
- [ ] `git push` to `origin/master` (GitHub: TechNaom/enterprise-knowledge-assistant)
- [ ] (Optional) confirm the live Streamlit Cloud URL is up with the Gemini key.
