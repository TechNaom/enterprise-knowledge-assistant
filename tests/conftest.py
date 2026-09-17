"""Shared pytest fixtures and a deterministic, offline fake provider.

The ``FakeProvider`` lets the whole pipeline run in tests without any network
call or model server:

* ``embed_texts`` — a bag-of-words hashing embedding (shared vocabulary ->
  similar vectors), which is deterministic yet gives meaningful similarity.
* ``chat`` — canned, prompt-aware responses (multi-query, re-rank, condense,
  answer) so retrieval and generation are fully reproducible.
"""

from __future__ import annotations

import hashlib
import math
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eka.config import Settings  # noqa: E402
from eka.indexer import build_index  # noqa: E402
from eka.rag import RAGPipeline  # noqa: E402

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class FakeProvider:
    """Deterministic, network-free provider for tests."""

    name = "fake"
    dim = 512

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _tokens(text):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def chat(self, system: str, user: str, temperature: float = 0.1) -> str:
        low = user.lower()
        if "index:score" in low or "index:score" in system.lower():
            return self._rerank(user)
        if "alternative phrasings" in low:
            return ""  # no extra queries -> pipeline keeps the original
        if "standalone question" in low:
            return self._condense(user)
        return self._answer(user)

    # -- canned behaviours --------------------------------------------------
    def _question(self, user: str) -> str:
        m = re.search(r"Question:\s*(.+)", user)
        return m.group(1).strip() if m else user

    def _rerank(self, user: str) -> str:
        """Score each passage by token overlap with the question."""
        question = set(_tokens(self._question(user)))
        lines = []
        for m in re.finditer(r"\[(\d+)\]\s*(.+?)(?=\n\[\d+\]|\Z)", user, re.S):
            idx = int(m.group(1))
            overlap = len(question & set(_tokens(m.group(2))))
            score = min(overlap, 10)
            lines.append(f"{idx}:{score}")
        return "\n".join(lines)

    def _condense(self, user: str) -> str:
        return self._question(user)

    def _answer(self, user: str) -> str:
        # Echo the first context block so answers reflect retrieved content.
        m = re.search(r"\[1\][^\n]*\n(.+?)(?=\n\[2\]|\nQuestion:|\Z)", user, re.S)
        body = m.group(1).strip() if m else "No relevant context."
        return f"{body[:280]} [1]"


@pytest.fixture(scope="session")
def fake_settings() -> Settings:
    s = Settings()
    s.provider = "fake"
    return s


@pytest.fixture(scope="session")
def sample_docs_dir() -> Path:
    docs = ROOT / "data" / "documents"
    assert docs.exists() and any(docs.iterdir()), "sample documents missing"
    return docs


@pytest.fixture(scope="session")
def pipeline(tmp_path_factory, fake_settings, sample_docs_dir) -> RAGPipeline:
    """A fully-built pipeline over the sample docs using the fake provider."""
    storage = tmp_path_factory.mktemp("eka_storage")
    chroma_dir = storage / "chroma"
    bm25_path = storage / "bm25.pkl"
    provider = FakeProvider()
    build_index(
        settings=fake_settings,
        data_dir=sample_docs_dir,
        provider=provider,
        chroma_dir=chroma_dir,
        bm25_path=bm25_path,
        log=lambda _m: None,
    )
    return RAGPipeline(
        settings=fake_settings,
        provider=provider,
        chroma_dir=chroma_dir,
        bm25_path=bm25_path,
    )
