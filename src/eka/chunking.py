"""Split documents into overlapping, retrieval-sized chunks.

A small, dependency-free recursive splitter: it tries to break on the most
natural boundary available (paragraph -> line -> sentence -> word) so chunks
stay semantically coherent, then adds a character overlap so context that
straddles a boundary is not lost.  Each chunk keeps a back-reference to its
source document for citation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .loaders import Document

# Ordered from coarsest to finest separators.
_SEPARATORS = ["\n\n", "\n", ". ", " "]


@dataclass
class Chunk:
    """A retrieval unit: a slice of a document plus its provenance."""

    id: str
    text: str
    source: str
    doc_type: str
    chunk_index: int


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Greedy recursive-boundary splitter with character overlap."""
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    # Pick the finest separator that actually appears, walking coarse -> fine.
    separator = next((s for s in _SEPARATORS if s in text), "")
    pieces = text.split(separator) if separator else list(text)

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = piece if not current else current + separator + piece
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        # A single piece larger than chunk_size is split again recursively.
        if len(piece) > chunk_size:
            chunks.extend(_split_text(piece, chunk_size, overlap))
            current = ""
        else:
            current = piece
    if current:
        chunks.append(current)

    return _add_overlap(chunks, overlap)


def _add_overlap(chunks: list[str], overlap: int) -> list[str]:
    """Prepend the tail of each chunk to the next one for context continuity."""
    if overlap <= 0 or len(chunks) < 2:
        return chunks
    out = [chunks[0]]
    for prev, cur in zip(chunks, chunks[1:]):
        tail = prev[-overlap:]
        out.append((tail + " " + cur).strip())
    return out


def chunk_document(doc: Document, chunk_size: int, overlap: int) -> list[Chunk]:
    """Chunk one document, assigning stable ids of the form ``source::index``."""
    parts = _split_text(doc.text, chunk_size, overlap)
    return [
        Chunk(
            id=f"{doc.source}::{i}",
            text=part,
            source=doc.source,
            doc_type=doc.doc_type,
            chunk_index=i,
        )
        for i, part in enumerate(parts)
    ]


def chunk_documents(docs: list[Document], chunk_size: int, overlap: int) -> list[Chunk]:
    """Chunk a list of documents into a flat list of chunks."""
    chunks: list[Chunk] = []
    for doc in docs:
        chunks.extend(chunk_document(doc, chunk_size, overlap))
    return chunks
