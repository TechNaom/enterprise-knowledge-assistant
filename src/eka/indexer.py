"""Build the search indexes from a folder of documents.

The ingestion pipeline:

    load folder -> chunk -> embed (batched) -> Chroma (dense) + BM25 (sparse)

Both indexes are persisted so the app starts instantly on subsequent runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .bm25_index import BM25Index
from .chunking import chunk_documents
from .config import BM25_PATH, CHROMA_DIR, Settings, get_settings
from .loaders import load_folder
from .providers import get_provider
from .vectorstore import VectorStore

ProgressFn = Callable[[str], None]


@dataclass
class IngestReport:
    documents: int
    chunks: int
    provider: str


def _embed_in_batches(provider, texts: list[str], batch_size: int, log: ProgressFn):
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        vectors.extend(provider.embed_texts(batch))
        log(f"  embedded {min(start + batch_size, len(texts))}/{len(texts)} chunks")
    return vectors


def build_index(
    settings: Settings | None = None,
    data_dir: Path | None = None,
    log: ProgressFn = print,
    batch_size: int = 16,
) -> IngestReport:
    settings = settings or get_settings()
    from .config import DATA_DIR

    data_dir = data_dir or DATA_DIR

    log(f"Loading documents from {data_dir} ...")
    docs = load_folder(data_dir)
    if not docs:
        raise RuntimeError(
            f"No supported documents found in {data_dir}. "
            "Add .pdf/.md/.txt files (or run scripts/generate_sample_docs.py)."
        )
    log(f"Loaded {len(docs)} document(s).")

    chunks = chunk_documents(docs, settings.chunk_size, settings.chunk_overlap)
    log(f"Split into {len(chunks)} chunks. Embedding with {settings.summary()} ...")

    provider = get_provider(settings)
    embeddings = _embed_in_batches(
        provider, [c.text for c in chunks], batch_size, log
    )

    log("Writing dense vectors to ChromaDB ...")
    store = VectorStore(CHROMA_DIR, settings.collection_name)
    store.reset()
    store.add(chunks, embeddings)

    log("Building BM25 sparse index ...")
    bm25 = BM25Index()
    bm25.build(chunks)
    bm25.save(BM25_PATH)

    log(f"Done. {len(docs)} docs -> {len(chunks)} chunks indexed.")
    return IngestReport(len(docs), len(chunks), provider.name)
