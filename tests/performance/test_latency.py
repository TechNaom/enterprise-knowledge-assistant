"""Performance tests: pipeline overhead must stay within budget.

Run with the deterministic fake provider so we measure *our* code's overhead
(chunking, vector search, fusion, MMR) rather than model latency.
"""

import time

import pytest

pytestmark = pytest.mark.performance

# Generous ceilings for the code's own overhead (no model latency involved).
QUERY_BUDGET_S = 3.0
INGEST_BUDGET_S = 15.0


def test_single_query_overhead_within_budget(pipeline):
    # warm up (first query touches lazy Chroma internals)
    pipeline.retriever.retrieve("warm up query")
    start = time.perf_counter()
    pipeline.retriever.retrieve("How many vacation days do I get?")
    elapsed = time.perf_counter() - start
    assert elapsed < QUERY_BUDGET_S, f"retrieval took {elapsed:.2f}s"


def test_end_to_end_answer_within_budget(pipeline):
    start = time.perf_counter()
    pipeline.answer("What is the per diem for international travel?")
    elapsed = time.perf_counter() - start
    assert elapsed < QUERY_BUDGET_S, f"answer took {elapsed:.2f}s"


def test_throughput_several_queries(pipeline):
    questions = [
        "vacation days",
        "password policy",
        "per diem",
        "wellness stipend",
        "harassment policy",
    ]
    start = time.perf_counter()
    for q in questions:
        pipeline.retriever.retrieve(q)
    avg = (time.perf_counter() - start) / len(questions)
    assert avg < QUERY_BUDGET_S, f"avg retrieval {avg:.2f}s"
