"""Central configuration for the Enterprise Knowledge Assistant.

All settings are read from environment variables (optionally loaded from a
local ``.env`` file) so the same code runs unchanged on a laptop against
local Ollama and on a hosted platform against Gemini.  Nothing here is
secret; secrets (e.g. ``GOOGLE_API_KEY``) live only in the environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv() -> None:
    """Minimal .env loader (no third-party dependency).

    Reads ``KEY=VALUE`` lines from a ``.env`` file in the project root and
    puts them into ``os.environ`` without overwriting values already set.
    """
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


# --- Paths -----------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "documents"
STORAGE_DIR = PROJECT_ROOT / "storage"
CHROMA_DIR = STORAGE_DIR / "chroma"
BM25_PATH = STORAGE_DIR / "bm25.pkl"

_load_dotenv()


def _get(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    """Resolved runtime settings (immutable snapshot of the environment)."""

    # Which backend powers generation + embeddings: "ollama" or "gemini".
    provider: str = field(default_factory=lambda: _get("EKA_PROVIDER", "ollama").lower())

    # Ollama (local, open-source default).
    ollama_host: str = field(default_factory=lambda: _get("OLLAMA_HOST", "http://localhost:11434"))
    ollama_chat_model: str = field(default_factory=lambda: _get("OLLAMA_CHAT_MODEL", "llama3.2"))
    ollama_embed_model: str = field(default_factory=lambda: _get("OLLAMA_EMBED_MODEL", "nomic-embed-text"))

    # Gemini (hosted, used for the public live deployment).
    google_api_key: str = field(default_factory=lambda: _get("GOOGLE_API_KEY", ""))
    gemini_chat_model: str = field(default_factory=lambda: _get("GEMINI_CHAT_MODEL", "gemini-flash-lite-latest"))
    gemini_embed_model: str = field(default_factory=lambda: _get("GEMINI_EMBED_MODEL", "gemini-embedding-001"))

    # Chunking.
    chunk_size: int = field(default_factory=lambda: _get_int("EKA_CHUNK_SIZE", 900))
    chunk_overlap: int = field(default_factory=lambda: _get_int("EKA_CHUNK_OVERLAP", 150))

    # Retrieval.
    top_k: int = field(default_factory=lambda: _get_int("EKA_TOP_K", 4))
    dense_k: int = field(default_factory=lambda: _get_int("EKA_DENSE_K", 8))
    sparse_k: int = field(default_factory=lambda: _get_int("EKA_SPARSE_K", 8))
    rrf_k: int = field(default_factory=lambda: _get_int("EKA_RRF_K", 60))
    mmr_lambda: float = field(default_factory=lambda: _get_float("EKA_MMR_LAMBDA", 0.6))
    use_multi_query: bool = field(default_factory=lambda: _get("EKA_MULTI_QUERY", "true").lower() == "true")
    use_rerank: bool = field(default_factory=lambda: _get("EKA_RERANK", "true").lower() == "true")

    collection_name: str = field(default_factory=lambda: _get("EKA_COLLECTION", "company_docs"))

    def summary(self) -> str:
        if self.provider == "gemini":
            models = f"{self.gemini_chat_model} + {self.gemini_embed_model}"
        else:
            models = f"{self.ollama_chat_model} + {self.ollama_embed_model} @ {self.ollama_host}"
        return f"provider={self.provider} ({models})"


def get_settings() -> Settings:
    """Build a fresh Settings snapshot from the current environment."""
    return Settings()
