#!/usr/bin/env python3
"""CLI: build the search indexes from ``data/documents``.

Usage:
    python ingest.py                 # ingest data/documents with current .env
    python ingest.py --data ./mydocs # ingest a different folder
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from eka.config import get_settings  # noqa: E402
from eka.indexer import build_index  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest documents into the RAG index.")
    parser.add_argument("--data", type=Path, default=None, help="Document folder.")
    args = parser.parse_args()

    settings = get_settings()
    try:
        report = build_index(settings=settings, data_dir=args.data)
    except Exception as exc:  # surface a clean message, not a traceback
        print(f"\nIngestion failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"\nIndexed {report.documents} documents into "
        f"{report.chunks} chunks using provider '{report.provider}'."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
