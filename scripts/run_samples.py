#!/usr/bin/env python3
"""Run a set of representative questions and write samples/sample_output.md.

Demonstrates single-turn retrieval, a multi-turn conversation (memory), and a
grounded refusal for an out-of-scope question.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eka.memory import ConversationMemory  # noqa: E402
from eka.rag import RAGPipeline  # noqa: E402

SINGLE = [
    "How many paid vacation days do I get, and can I carry them over?",
    "How often must I change my password, and is MFA required?",
    "What is the per diem for international travel, and is alcohol reimbursable?",
]
MULTI = [
    "How much parental leave is there?",
    "And how long for partners?",
]
OUT_OF_SCOPE = "What is the company's stock price today?"


def _block(lines: list[str], ans) -> None:
    lines.append(ans.text.strip())
    if ans.sources:
        lines.append("\n**Sources:** " + ", ".join(
            f"{s.source} (chunk {s.chunk_index})" for s in ans.sources
        ))
    lines.append("\n---\n")


def main() -> int:
    p = RAGPipeline()
    if not p.is_ready():
        print("Index empty — run 'python ingest.py' first.", file=sys.stderr)
        return 1

    out = [
        "# Sample Output",
        "",
        f"Generated against the **Aveltra Technologies** sample documents "
        f"using provider `{p.settings.provider}`.",
        "",
        "## Single-turn questions",
        "",
    ]
    for q in SINGLE:
        print(f"[single] {q}")
        out.append(f"### Q: {q}\n")
        _block(out, p.answer(q))

    out.append("## Multi-turn conversation (memory)\n")
    mem = ConversationMemory()
    for q in MULTI:
        print(f"[multi] {q}")
        ans = p.answer(q, memory=mem)
        out.append(f"### Q: {q}")
        out.append(f"*(resolved to: “{ans.standalone_question}”)*\n")
        _block(out, ans)

    out.append("## Out-of-scope (grounded refusal)\n")
    print(f"[oos] {OUT_OF_SCOPE}")
    out.append(f"### Q: {OUT_OF_SCOPE}\n")
    _block(out, p.answer(OUT_OF_SCOPE))

    dest = ROOT / "samples" / "sample_output.md"
    dest.write_text("\n".join(out), encoding="utf-8")
    print(f"\nWrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
