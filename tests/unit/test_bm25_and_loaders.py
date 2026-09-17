"""Unit tests for the BM25 sparse index and document loaders."""

from pathlib import Path

import pytest

from eka.bm25_index import BM25Index
from eka.chunking import Chunk
from eka.loaders import load_document, load_folder


def _chunk(cid: str, text: str) -> Chunk:
    return Chunk(id=cid, text=text, source="s", doc_type="text", chunk_index=0)


def test_bm25_ranks_keyword_match_first():
    idx = BM25Index()
    idx.build([
        _chunk("vpn", "VPN and split tunnelling are disabled for remote access"),
        _chunk("leave", "annual leave and paid time off accrual"),
        _chunk("food", "per diem meal allowance for travel"),
    ])
    hits = idx.query("VPN split tunnelling", k=3)
    assert hits
    assert hits[0].id == "vpn"


def test_bm25_empty_index_returns_nothing():
    assert BM25Index().query("anything", k=5) == []


def test_bm25_save_and_load(tmp_path: Path):
    idx = BM25Index()
    idx.build([_chunk("a", "hello world"), _chunk("b", "foo bar baz")])
    p = tmp_path / "bm25.pkl"
    idx.save(p)
    loaded = BM25Index.load(p)
    hits = loaded.query("hello", k=2)
    assert hits and hits[0].id == "a"


def test_loader_reads_sample_pdf_and_markdown():
    docs_dir = Path(__file__).resolve().parents[2] / "data" / "documents"
    docs = load_folder(docs_dir)
    types = {d.doc_type for d in docs}
    assert "pdf" in types and "text" in types  # both required formats present
    assert all(d.text.strip() for d in docs)   # no empty documents


def test_loader_skips_unsupported(tmp_path: Path):
    (tmp_path / "note.md").write_text("# hi\ncontent", encoding="utf-8")
    (tmp_path / "data.csv").write_text("a,b,c", encoding="utf-8")
    docs = load_folder(tmp_path)
    assert len(docs) == 1 and docs[0].doc_type == "text"


def test_loader_missing_folder_raises():
    with pytest.raises(FileNotFoundError):
        load_folder(Path("/no/such/folder/xyz"))
