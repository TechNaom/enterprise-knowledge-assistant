"""Load documents from a local folder.

Supports the two required formats out of the box:

* **PDF**  (``.pdf``) via :mod:`pypdf`
* **Markdown / plain text** (``.md``, ``.markdown``, ``.txt``)

Each file becomes one :class:`Document` (full text + source metadata).  The
loader walks a directory recursively and skips unsupported extensions, so you
can drop a mixed folder of company documents straight in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader

TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
PDF_SUFFIXES = {".pdf"}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | PDF_SUFFIXES


@dataclass
class Document:
    """A single source document loaded from disk."""

    text: str
    source: str  # human-friendly file name, used in citations
    path: str
    doc_type: str  # "pdf" or "text"
    metadata: dict = field(default_factory=dict)


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(pages).strip()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def load_document(path: Path) -> Document | None:
    """Load a single file into a :class:`Document`, or ``None`` if unsupported."""
    suffix = path.suffix.lower()
    if suffix in PDF_SUFFIXES:
        text, doc_type = _read_pdf(path), "pdf"
    elif suffix in TEXT_SUFFIXES:
        text, doc_type = _read_text(path), "text"
    else:
        return None
    if not text:
        return None
    return Document(text=text, source=path.name, path=str(path), doc_type=doc_type)


def load_folder(folder: Path) -> list[Document]:
    """Recursively load every supported document under ``folder``."""
    folder = Path(folder)
    if not folder.exists():
        raise FileNotFoundError(f"Document folder not found: {folder}")
    docs: list[Document] = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            doc = load_document(path)
            if doc is not None:
                docs.append(doc)
    return docs
