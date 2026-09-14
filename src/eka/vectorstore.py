"""ChromaDB-backed dense vector store.

We drive the embeddings ourselves (via the selected :mod:`providers` backend)
and hand pre-computed vectors to Chroma, so the store is fully local and does
not download Chroma's default embedding model.  Chroma persists to disk under
``storage/chroma`` so the index survives restarts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from .chunking import Chunk


@dataclass
class Retrieved:
    """A chunk returned by retrieval, with its score and provenance."""

    id: str
    text: str
    source: str
    doc_type: str
    chunk_index: int
    score: float = 0.0


class VectorStore:
    """Thin wrapper over a persistent Chroma collection."""

    def __init__(self, persist_dir: Path, collection_name: str) -> None:
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self) -> None:
        """Drop and recreate the collection (used before a fresh ingest)."""
        name = self._collection.name
        self._client.delete_collection(name)
        self._collection = self._client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )

    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """Add chunks and their embeddings to the collection."""
        if not chunks:
            return
        self._collection.add(
            ids=[c.id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "source": c.source,
                    "doc_type": c.doc_type,
                    "chunk_index": c.chunk_index,
                }
                for c in chunks
            ],
        )

    def count(self) -> int:
        return self._collection.count()

    def query(self, embedding: list[float], k: int) -> list[Retrieved]:
        """Return the ``k`` nearest chunks to a query embedding."""
        if self.count() == 0:
            return []
        res = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        out: list[Retrieved] = []
        ids = res["ids"][0]
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]
        for cid, text, meta, dist in zip(ids, docs, metas, dists):
            # cosine distance -> similarity in [0, 1]
            out.append(
                Retrieved(
                    id=cid,
                    text=text,
                    source=str(meta.get("source", "unknown")),
                    doc_type=str(meta.get("doc_type", "text")),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    score=1.0 - float(dist),
                )
            )
        return out
