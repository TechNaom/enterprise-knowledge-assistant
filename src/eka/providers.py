"""LLM + embedding provider abstraction.

A single small interface (:class:`Provider`) hides the difference between the
local, open-source **Ollama** backend and the hosted **Gemini** backend.  The
rest of the codebase depends only on ``embed_texts`` and ``chat`` — swapping
provider is a one-line config change (``EKA_PROVIDER``), which is what lets the
same app run locally and as a public live deployment.
"""

from __future__ import annotations

import time
from typing import Callable, Protocol, TypeVar

from .config import Settings

T = TypeVar("T")


def _with_retry(fn: Callable[[], T], attempts: int = 4, base_delay: float = 1.5) -> T:
    """Retry a call on transient (429/503) errors with exponential backoff."""
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - inspect message for transient codes
            msg = str(exc)
            transient = any(code in msg for code in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"))
            last_exc = exc
            if not transient or i == attempts - 1:
                raise
            time.sleep(base_delay * (2**i))
    assert last_exc is not None
    raise last_exc


class Provider(Protocol):
    """Minimal capability set the RAG pipeline needs from a backend."""

    name: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return an embedding vector for each input text."""
        ...

    def chat(self, system: str, user: str, temperature: float = 0.1) -> str:
        """Return the model's reply to a system + user message pair."""
        ...


class OllamaProvider:
    """Local, open-source backend using an Ollama server (default)."""

    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        import ollama

        self._client = ollama.Client(host=settings.ollama_host)
        self._chat_model = settings.ollama_chat_model
        self._embed_model = settings.ollama_embed_model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # Ollama's embed endpoint accepts a batch and returns one vector each.
        resp = self._client.embed(model=self._embed_model, input=texts)
        return [list(v) for v in resp["embeddings"]]

    def chat(self, system: str, user: str, temperature: float = 0.1) -> str:
        resp = self._client.chat(
            model=self._chat_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            options={"temperature": temperature},
        )
        return resp["message"]["content"].strip()


class GeminiProvider:
    """Hosted backend using Google Gemini (used for the live deployment)."""

    name = "gemini"

    def __init__(self, settings: Settings) -> None:
        from google import genai

        if not settings.google_api_key:
            raise RuntimeError(
                "EKA_PROVIDER=gemini requires GOOGLE_API_KEY to be set."
            )
        self._client = genai.Client(api_key=settings.google_api_key)
        self._chat_model = settings.gemini_chat_model
        self._embed_model = settings.gemini_embed_model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        resp = _with_retry(
            lambda: self._client.models.embed_content(
                model=self._embed_model, contents=texts
            )
        )
        return [list(e.values) for e in resp.embeddings]

    def chat(self, system: str, user: str, temperature: float = 0.1) -> str:
        from google.genai import types

        resp = _with_retry(
            lambda: self._client.models.generate_content(
                model=self._chat_model,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=temperature,
                ),
            )
        )
        return (resp.text or "").strip()


def get_provider(settings: Settings) -> Provider:
    """Instantiate the provider selected by ``settings.provider``."""
    if settings.provider == "gemini":
        return GeminiProvider(settings)
    if settings.provider == "ollama":
        return OllamaProvider(settings)
    raise ValueError(
        f"Unknown EKA_PROVIDER={settings.provider!r} (expected 'ollama' or 'gemini')."
    )
