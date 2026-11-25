"""Shared dependencies for API routes."""

from functools import lru_cache
from typing import Optional

from sqlalchemy.orm import Session

from core.rag_engine import build_rag_chain, load_rag_chain
from core.vector_store import has_session_vectors
from db.repository import get_analysis_by_session_id
from utils.llm import get_llm


# ── In-memory session store for RAG chains ──────────────────────────
# Maps session_id → rag_chain runnable (populated on index/pipeline or
# lazily reconstructed from persistent ChromaDB after a server restart).
rag_sessions: dict[str, object] = {}


@lru_cache(maxsize=1)
def get_cached_llm():
    """Return a singleton LLM instance (cached across requests)."""
    return get_llm()


def get_or_restore_rag_chain(
    session_id: str,
    db: Optional[Session] = None,
) -> Optional[object]:
    """Return an active RAG chain, reconstructing it from ChromaDB if needed."""
    if not session_id:
        return None

    if session_id in rag_sessions:
        return rag_sessions[session_id]

    if has_session_vectors(session_id):
        llm = get_cached_llm()
        rag_chain = load_rag_chain(llm=llm, session_id=session_id)
        rag_sessions[session_id] = rag_chain
        return rag_chain

    # Fallback: if vectors are missing (e.g. deleted vector_db) but analysis exists in SQLite
    if db is not None:
        record = get_analysis_by_session_id(db, session_id)
        if record is not None and record.transcript.strip():
            llm = get_cached_llm()
            rag_chain = build_rag_chain(
                llm=llm,
                transcript=record.transcript,
                video_id=record.video_id or session_id,
                video_title=record.title,
                session_id=session_id,
            )
            rag_sessions[session_id] = rag_chain
            return rag_chain

    return None
