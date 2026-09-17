"""Unit tests for the fusion / diversification math (RRF, MMR, cosine)."""

from eka.config import Settings
from eka.retriever import HybridRetriever, _cosine
from eka.vectorstore import Retrieved


def _r(rid: str, score: float = 0.0) -> Retrieved:
    return Retrieved(id=rid, text=rid, source="s", doc_type="text",
                     chunk_index=0, score=score)


def _retriever() -> HybridRetriever:
    # store/bm25 unused by the pure math methods
    return HybridRetriever(Settings(), provider=None, store=None, bm25=None)


def test_cosine_basic():
    assert _cosine([1, 0], [1, 0]) == 1.0
    assert _cosine([1, 0], [0, 1]) == 0.0
    assert abs(_cosine([1, 1], [1, 0]) - 0.7071) < 1e-3


def test_cosine_handles_zero_vector():
    assert _cosine([0, 0], [1, 1]) == 0.0


def test_rrf_rewards_agreement_across_lists():
    r = _retriever()
    dense = [_r("A"), _r("B"), _r("C")]
    sparse = [_r("B"), _r("A"), _r("D")]
    fused = r._rrf([dense, sparse])
    ids = [x.id for x in fused]
    # A and B appear high in both -> ranked above C and D
    assert set(ids[:2]) == {"A", "B"}
    assert ids[-1] in {"C", "D"}


def test_rrf_deduplicates():
    r = _retriever()
    fused = r._rrf([[_r("A"), _r("B")], [_r("A")]])
    assert sorted(x.id for x in fused) == ["A", "B"]


def test_mmr_selects_relevant_first():
    r = _retriever()
    cands = [_r("A"), _r("B"), _r("C")]
    relevance = {"A": 0.9, "B": 0.5, "C": 0.1}
    vecs = {"A": [1, 0, 0], "B": [0, 1, 0], "C": [0, 0, 1]}
    out = r._mmr(relevance, cands, vecs, k=2)
    assert out[0].id == "A"  # most relevant chosen first


def test_mmr_penalises_redundancy():
    r = _retriever()
    # A and B are identical vectors (redundant); C is different.
    cands = [_r("A"), _r("B"), _r("C")]
    relevance = {"A": 0.9, "B": 0.85, "C": 0.4}
    vecs = {"A": [1, 0], "B": [1, 0], "C": [0, 1]}
    out = r._mmr(relevance, cands, vecs, k=2)
    ids = [x.id for x in out]
    assert ids[0] == "A"
    # despite lower relevance, diverse C beats redundant B for the 2nd slot
    assert ids[1] == "C"
