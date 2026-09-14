"""Advanced hybrid retriever.

This is what lifts the app above a basic "chat with PDF".  A single query flows
through several techniques:

1. **Multi-query expansion** — the LLM rewrites the query into several phrasings
   to widen recall (optional, ``EKA_MULTI_QUERY``).
2. **Dense retrieval** — semantic vector search over ChromaDB.
3. **Sparse retrieval** — BM25 keyword search (catches exact terms/acronyms).
4. **Reciprocal Rank Fusion (RRF)** — merges the dense + sparse rankings into a
   single robust list without needing to calibrate score scales.
5. **LLM re-ranking** — the model scores the top fused candidates for relevance
   (optional, ``EKA_RERANK``).
6. **MMR diversification** — greedily selects a final set that is both relevant
   and non-redundant, so the context isn't three copies of the same paragraph.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .bm25_index import BM25Index
from .config import Settings
from .prompts import MULTI_QUERY_PROMPT, RERANK_PROMPT
from .providers import Provider
from .vectorstore import Retrieved, VectorStore


@dataclass
class RetrievalTrace:
    """Diagnostics about a retrieval, surfaced in the UI for transparency."""

    expanded_queries: list[str]
    dense_hits: int
    sparse_hits: int
    fused_hits: int
    reranked: bool


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class HybridRetriever:
    """Dense + sparse retrieval fused with RRF, then reranked and diversified."""

    def __init__(
        self,
        settings: Settings,
        provider: Provider,
        store: VectorStore,
        bm25: BM25Index,
    ) -> None:
        self.settings = settings
        self.provider = provider
        self.store = store
        self.bm25 = bm25

    # -- query expansion ----------------------------------------------------
    def _expand_queries(self, query: str) -> list[str]:
        if not self.settings.use_multi_query:
            return [query]
        try:
            raw = self.provider.chat(
                system="You rewrite search queries. Reply with plain lines only.",
                user=MULTI_QUERY_PROMPT.format(n=3, question=query),
                temperature=0.3,
            )
        except Exception:
            return [query]
        extra = [line.strip("-• ").strip() for line in raw.splitlines() if line.strip()]
        # Always keep the original query first; de-duplicate case-insensitively.
        seen, queries = set(), []
        for q in [query, *extra]:
            key = q.lower()
            if q and key not in seen:
                seen.add(key)
                queries.append(q)
        return queries[:4]

    # -- fusion -------------------------------------------------------------
    def _rrf(self, ranked_lists: list[list[Retrieved]]) -> list[Retrieved]:
        """Reciprocal Rank Fusion across several ranked result lists."""
        k = self.settings.rrf_k
        scores: dict[str, float] = {}
        best: dict[str, Retrieved] = {}
        for results in ranked_lists:
            for rank, item in enumerate(results):
                scores[item.id] = scores.get(item.id, 0.0) + 1.0 / (k + rank + 1)
                best.setdefault(item.id, item)
        fused = []
        for cid, score in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
            item = best[cid]
            fused.append(
                Retrieved(
                    id=item.id,
                    text=item.text,
                    source=item.source,
                    doc_type=item.doc_type,
                    chunk_index=item.chunk_index,
                    score=score,
                )
            )
        return fused

    # -- reranking ----------------------------------------------------------
    def _rerank(self, query: str, candidates: list[Retrieved]) -> list[Retrieved]:
        """Score all candidates in ONE LLM call; set each ``score`` to the
        LLM relevance (0-1) and return them re-ordered by that score."""
        passages = "\n\n".join(
            f"[{i}] {c.text[:600]}" for i, c in enumerate(candidates)
        )
        # Fallback scores preserve the incoming (fused) order if parsing fails.
        n = len(candidates)
        scores: dict[int, float] = {i: (n - i) / n for i in range(n)}
        try:
            reply = self.provider.chat(
                system="You are a strict relevance judge. Output only 'index:score' lines.",
                user=RERANK_PROMPT.format(question=query, passages=passages),
                temperature=0.0,
            )
            for line in reply.splitlines():
                if ":" not in line:
                    continue
                idx_s, _, score_s = line.partition(":")
                idx_digits = "".join(ch for ch in idx_s if ch.isdigit())
                score_digits = "".join(ch for ch in score_s if ch.isdigit())
                if idx_digits and score_digits:
                    idx = int(idx_digits)
                    if idx in scores:
                        scores[idx] = min(int(score_digits), 10) / 10.0
        except Exception:
            pass
        for i, cand in enumerate(candidates):
            cand.score = scores[i]
        order = sorted(range(n), key=lambda i: scores[i], reverse=True)
        return [candidates[i] for i in order]

    # -- diversification ----------------------------------------------------
    def _mmr(
        self,
        relevance: dict[str, float],
        candidates: list[Retrieved],
        cand_vecs: dict[str, list[float]],
        k: int,
    ) -> list[Retrieved]:
        """Maximal Marginal Relevance: balance relevance against redundancy.

        ``relevance`` is the per-candidate relevance signal (the re-ranker's
        score when available, else query-document cosine), so MMR only removes
        *redundancy* rather than second-guessing the relevance judgement.
        """
        lam = self.settings.mmr_lambda
        selected: list[Retrieved] = []
        pool = list(candidates)
        while pool and len(selected) < k:
            best_item, best_score = None, -1e9
            for cand in pool:
                vec = cand_vecs.get(cand.id, [])
                rel = relevance.get(cand.id, cand.score)
                redundancy = max(
                    (_cosine(vec, cand_vecs.get(s.id, [])) for s in selected),
                    default=0.0,
                )
                score = lam * rel - (1 - lam) * redundancy
                if score > best_score:
                    best_item, best_score = cand, score
            selected.append(best_item)
            pool.remove(best_item)
        return selected

    # -- public API ---------------------------------------------------------
    def retrieve(self, query: str) -> tuple[list[Retrieved], RetrievalTrace]:
        queries = self._expand_queries(query)

        # Embed all query variants in one batch, dense-search each.
        q_embeddings = self.provider.embed_texts(queries)
        dense_lists: list[list[Retrieved]] = [
            self.store.query(emb, self.settings.dense_k) for emb in q_embeddings
        ]
        sparse_lists: list[list[Retrieved]] = [
            self.bm25.query(q, self.settings.sparse_k) for q in queries
        ]

        dense_hits = sum(len(x) for x in dense_lists)
        sparse_hits = sum(len(x) for x in sparse_lists)

        fused = self._rrf([*dense_lists, *sparse_lists])
        if not fused:
            return [], RetrievalTrace(queries, dense_hits, sparse_hits, 0, False)

        # Consider a generous candidate window before the final selection.
        window = fused[: max(self.settings.top_k * 3, 10)]

        # MMR needs vectors for the candidates; embed them once.
        cand_vecs_list = self.provider.embed_texts([c.text for c in window])
        cand_vecs = {c.id: v for c, v in zip(window, cand_vecs_list)}
        query_vec = q_embeddings[0]

        reranked = False
        if self.settings.use_rerank and len(window) > self.settings.top_k:
            window = self._rerank(query, window)
            reranked = True
            # relevance = the re-ranker's score (set on each candidate).
            relevance = {c.id: c.score for c in window}
        else:
            # relevance = query-document cosine similarity.
            relevance = {c.id: _cosine(query_vec, cand_vecs.get(c.id, [])) for c in window}

        final = self._mmr(relevance, window, cand_vecs, self.settings.top_k)

        trace = RetrievalTrace(
            expanded_queries=queries,
            dense_hits=dense_hits,
            sparse_hits=sparse_hits,
            fused_hits=len(fused),
            reranked=reranked,
        )
        return final, trace
