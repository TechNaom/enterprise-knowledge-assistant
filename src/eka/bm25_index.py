"""BM25 sparse (keyword) index.

Dense vector search is strong on meaning but can miss exact terms — policy
numbers, acronyms (``PTO``, ``VPN``), or specific phrases.  A classic BM25
keyword index complements it, and fusing the two (see :mod:`retriever`) is what
makes retrieval robust.  The index is small enough to keep in memory and
pickle to disk alongside the vector store.
"""

from __future__ import annotations

import pickle
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from .chunking import Chunk
from .vectorstore import Retrieved

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    """In-memory BM25 index over chunk text with pickle persistence."""

    def __init__(self) -> None:
        self._bm25: BM25Okapi | None = None
        self._chunks: list[Chunk] = []

    def build(self, chunks: list[Chunk]) -> None:
        self._chunks = list(chunks)
        corpus = [_tokenize(c.text) for c in chunks]
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def query(self, text: str, k: int) -> list[Retrieved]:
        if self._bm25 is None or not self._chunks:
            return []
        scores = self._bm25.get_scores(_tokenize(text))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        out: list[Retrieved] = []
        for i in ranked[:k]:
            if scores[i] <= 0:
                continue
            c = self._chunks[i]
            out.append(
                Retrieved(
                    id=c.id,
                    text=c.text,
                    source=c.source,
                    doc_type=c.doc_type,
                    chunk_index=c.chunk_index,
                    score=float(scores[i]),
                )
            )
        return out

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as fh:
            pickle.dump({"bm25": self._bm25, "chunks": self._chunks}, fh)

    @classmethod
    def load(cls, path: Path) -> "BM25Index":
        obj = cls()
        if path.exists():
            with path.open("rb") as fh:
                data = pickle.load(fh)
            obj._bm25 = data["bm25"]
            obj._chunks = data["chunks"]
        return obj
