"""Multi-turn conversation memory.

Two responsibilities:

* Keep a rolling window of recent turns so the assistant has context.
* **History-aware query condensing** — rewrite a follow-up ("what about for
  interns?") into a standalone question before retrieval, so the retriever
  searches for the right thing instead of the literal follow-up.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .prompts import CONDENSE_QUESTION_PROMPT
from .providers import Provider


@dataclass
class Turn:
    role: str  # "user" or "assistant"
    content: str


@dataclass
class ConversationMemory:
    """A bounded history of turns with a condensing helper."""

    max_turns: int = 8
    turns: list[Turn] = field(default_factory=list)

    def add_user(self, content: str) -> None:
        self.turns.append(Turn("user", content))
        self._trim()

    def add_assistant(self, content: str) -> None:
        self.turns.append(Turn("assistant", content))
        self._trim()

    def _trim(self) -> None:
        if len(self.turns) > self.max_turns * 2:
            self.turns = self.turns[-self.max_turns * 2 :]

    def as_text(self) -> str:
        return "\n".join(f"{t.role.capitalize()}: {t.content}" for t in self.turns)

    def condense(self, provider: Provider, question: str) -> str:
        """Rewrite a follow-up into a standalone question using history."""
        if not self.turns:
            return question
        history = self.as_text()
        try:
            rewritten = provider.chat(
                system="You rewrite follow-up questions into standalone ones.",
                user=CONDENSE_QUESTION_PROMPT.format(history=history, question=question),
                temperature=0.0,
            )
        except Exception:
            return question
        rewritten = rewritten.strip()
        return rewritten or question
