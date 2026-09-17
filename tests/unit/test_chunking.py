"""Unit tests for the document chunker."""

from eka.chunking import chunk_document, chunk_documents
from eka.loaders import Document


def _doc(text: str) -> Document:
    return Document(text=text, source="d.md", path="d.md", doc_type="text")


def test_short_document_is_single_chunk():
    chunks = chunk_document(_doc("A short policy."), chunk_size=900, overlap=150)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].source == "d.md"


def test_long_document_is_split():
    text = "\n\n".join(f"Paragraph {i} " + "word " * 40 for i in range(10))
    chunks = chunk_document(_doc(text), chunk_size=300, overlap=50)
    assert len(chunks) > 1
    # ids are stable and ordered
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    assert chunks[0].id == "d.md::0"


def test_chunks_respect_size_budget_roughly():
    text = "word " * 1000
    chunks = chunk_document(_doc(text), chunk_size=200, overlap=20)
    # allow overlap slack, but no chunk should be wildly oversized
    assert all(len(c.text) <= 200 + 60 for c in chunks)


def test_chunk_documents_flattens():
    docs = [_doc("one two three"), _doc("four five six")]
    chunks = chunk_documents(docs, chunk_size=900, overlap=100)
    assert len(chunks) == 2


def test_empty_document_yields_no_chunks():
    assert chunk_document(_doc("   "), 900, 150) == []
