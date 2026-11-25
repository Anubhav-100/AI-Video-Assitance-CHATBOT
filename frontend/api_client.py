
import os
import requests
from typing import Any, Dict, List, Optional


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


def _get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
    response = requests.get(f"{BASE_URL.rstrip('/')}{endpoint}", params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def _delete(endpoint: str) -> Dict[str, Any]:
    response = requests.delete(f"{BASE_URL.rstrip('/')}{endpoint}", timeout=TIMEOUT)
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
# History API
# ---------------------------------------------------------------------------

def save_analysis_history(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Save a completed analysis record to persistent backend history."""
    return _post("/history", payload)


def list_analysis_history(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Fetch saved analyses ordered newest first."""
    return _get("/history", params={"limit": limit, "offset": offset})


def get_analysis_history(analysis_id: int) -> Dict[str, Any]:
    """Retrieve a complete saved analysis by ID."""
    return _get(f"/history/{analysis_id}")


def delete_analysis_history(analysis_id: int) -> Dict[str, Any]:
    """Delete a saved analysis by ID."""
    return _delete(f"/history/{analysis_id}")


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def analyze_video(source: str, engine: str = "whisper") -> Dict[str, Any]:

    """Convenience wrapper for video analysis."""

    return run_pipeline(source, engine)
