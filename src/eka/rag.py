"""The end-to-end RAG pipeline.

Ties everything together: load the indexes, retrieve context for a question
(optionally condensed against conversation history), and generate a grounded,
cited answer.  This is the single object the UI and CLI talk to.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bm25_index import BM25Index
from .config import Settings, get_settings
from .memory import ConversationMemory
from .prompts import ANSWER_SYSTEM_PROMPT, ANSWER_USER_PROMPT
from .providers import Provider, get_provider
from .retriever import HybridRetriever, RetrievalTrace
from .vectorstore import Retrieved, VectorStore


@dataclass
class Answer:
    """A generated answer plus the evidence and diagnostics behind it."""

    text: str
    sources: list[Retrieved]
    standalone_question: str
    trace: RetrievalTrace


def _format_context(chunks: list[Retrieved]) -> str:
    """Number the retrieved chunks so the model can cite them as [n]."""
    blocks = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(f"[{i}] (source: {c.source})\n{c.text}")
    return "\n\n".join(blocks)


class RAGPipeline:
    """Load-once, ask-many RAG engine."""

    def __init__(
        self,
        settings: Settings | None = None,
        provider: Provider | None = None,
        chroma_dir=None,
        bm25_path=None,
    ) -> None:
        self.settings = settings or get_settings()
        self.provider: Provider = provider or get_provider(self.settings)
        from .config import BM25_PATH, CHROMA_DIR

        self.store = VectorStore(
            chroma_dir or CHROMA_DIR, self.settings.collection_name
        )
        self.bm25 = BM25Index.load(bm25_path or BM25_PATH)
        self.retriever = HybridRetriever(
            self.settings, self.provider, self.store, self.bm25
        )

    def is_ready(self) -> bool:
        """True when documents have been ingested and can be queried."""
        return self.store.count() > 0

    def answer(
        self, question: str, memory: ConversationMemory | None = None
    ) -> Answer:
        # Resolve follow-ups against history before retrieval.
        standalone = (
            memory.condense(self.provider, question) if memory else question
        )
        chunks, trace = self.retriever.retrieve(standalone)

        if not chunks:
            text = (
                "I couldn't find anything about that in the company documents. "
                "Please rephrase, or contact HR/IT if this is an urgent policy question."
            )
            return Answer(text, [], standalone, trace)

        context = _format_context(chunks)
        text = self.provider.chat(
            system=ANSWER_SYSTEM_PROMPT,
            user=ANSWER_USER_PROMPT.format(context=context, question=standalone),
            temperature=0.1,
        )
        if memory is not None:
            memory.add_user(question)
            memory.add_assistant(text)
        return Answer(text, chunks, standalone, trace)
