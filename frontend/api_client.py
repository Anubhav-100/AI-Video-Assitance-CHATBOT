
import os
import requests
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("AI_VIDEO_API_URL", "http://localhost:8000/api/v1")
TIMEOUT = 600

# ---------------------------------------------------------------------------
# Internal API helper
# ---------------------------------------------------------------------------

def _post(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(f"{BASE_URL.rstrip('/')}{endpoint}", json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()

# ---------------------------------------------------------------------------
# Pipeline API
# ---------------------------------------------------------------------------

def run_pipeline(source: str, engine: str = "whisper", session_id: Optional[str] = None) -> Dict[str, Any]:

    """Run the complete video/audio processing pipeline."""

    payload = {
        "source": source,
        "engine": engine,
        "session_id": session_id,
    }

    return _post("/pipeline", payload)


# ---------------------------------------------------------------------------
# RAG API
# ---------------------------------------------------------------------------

def rag_index(transcript: str, video_id: str, video_title: str, session_id: str) -> Dict[str, Any]:

    """Index transcript through the FastAPI backend."""

    payload = {
        "transcript": transcript,
        "video_id": video_id,
        "video_title": video_title,
        "session_id": session_id,
    }

    return _post("/rag/index", payload)


def rag_query(session_id: str, question: str) -> str:

    """Query the indexed transcript through FastAPI."""

    payload = {
        "session_id": session_id,
        "question": question,
    }

    response = _post("/rag/query", payload)

    return response["answer"]


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def analyze_video(source: str, engine: str = "whisper") -> Dict[str, Any]:

    """Convenience wrapper for video analysis."""

    return run_pipeline(source, engine)
