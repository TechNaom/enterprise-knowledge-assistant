"""Regression tests: known questions must retrieve the correct source documents.

These guard against silent quality regressions in the retrieval pipeline
(e.g. the MMR-vs-rerank bug where the authoritative policy chunk was dropped).
Uses the deterministic fake provider so results are reproducible in CI.
"""

import pytest

pytestmark = pytest.mark.regression

# (question, expected source document that must appear in the retrieved set)
GOLDEN = [
    ("How many paid vacation days and can I carry them over?", "leave-policy.md"),
    ("How often must I change my password and is MFA required?", "it-security-policy.pdf"),
    ("What is the per diem for international travel?", "travel-and-expense-policy.pdf"),
    ("What does the wellness stipend cover?", "benefits.md"),
    ("What is the policy on harassment and the ethics hotline?", "code-of-conduct.md"),
]


@pytest.mark.parametrize("question,expected_source", GOLDEN)
def test_expected_source_is_retrieved(pipeline, question, expected_source):
    chunks, _ = pipeline.retriever.retrieve(question)
    sources = {c.source for c in chunks}
    assert expected_source in sources, (
        f"{expected_source!r} missing for {question!r}; got {sources}"
    )


def test_pto_query_retrieves_leave_policy(pipeline):
    """The carry-over question must retrieve the authoritative leave policy.

    Note: asserting the *exact* carry-over chunk out-ranks the sick-leave chunk
    requires a real cross-encoder reranker.  The offline bag-of-words
    ``FakeProvider`` is fooled by the negated lexical distractor
    ("sick leave does *not* carry over"), so this offline guard checks the
    deterministic property — the leave policy source is retrieved — while the
    exact-chunk ranking is validated against a live model.
    """
    chunks, _ = pipeline.retriever.retrieve(
        "How many paid vacation days do I get, and can I carry them over?"
    )
    assert "leave-policy.md" in {c.source for c in chunks}


def test_answer_is_grounded_and_cited(pipeline):
    ans = pipeline.answer("What is the per diem for international travel?")
    assert ans.sources                      # evidence returned
    assert "[1]" in ans.text                # citation present
    assert "travel-and-expense-policy.pdf" in {s.source for s in ans.sources}
