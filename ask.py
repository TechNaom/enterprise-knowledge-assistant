#!/usr/bin/env python3
"""CLI: ask the Enterprise Knowledge Assistant a question from the terminal.

Usage:
    python ask.py "How many vacation days do I get?"
    python ask.py            # interactive loop (keeps conversation memory)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from eka.memory import ConversationMemory  # noqa: E402
from eka.rag import RAGPipeline  # noqa: E402


def _print_answer(ans) -> None:
    print("\n" + ans.text + "\n")
    if ans.sources:
        print("Sources:")
        for i, s in enumerate(ans.sources, start=1):
            print(f"  [{i}] {s.source} (chunk {s.chunk_index})")
    print("-" * 60)


def main() -> int:
    pipeline = RAGPipeline()
    if not pipeline.is_ready():
        print("Index is empty. Run 'python ingest.py' first.", file=sys.stderr)
        return 1

    if len(sys.argv) > 1:  # one-shot mode
        _print_answer(pipeline.answer(" ".join(sys.argv[1:])))
        return 0

    memory = ConversationMemory()
    print("Enterprise Knowledge Assistant (type 'exit' to quit)\n")
    while True:
        try:
            q = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"exit", "quit"}:
            break
        if q:
            _print_answer(pipeline.answer(q, memory=memory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
