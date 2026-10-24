"""Shared dependencies for API routes."""

from functools import lru_cache
from utils.llm import get_llm


# ── In-memory session store for RAG chains ──────────────────────────
# Maps session_id → rag_chain runnable.
# In production you'd replace this with Redis or a proper session backend.
rag_sessions: dict[str, object] = {}


@lru_cache(maxsize=1)
def get_cached_llm():
    """Return a singleton LLM instance (cached across requests)."""
    return get_llm()
