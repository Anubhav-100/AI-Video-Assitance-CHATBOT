"""
Pytest suite for the FastAPI REST API endpoints.
Uses unittest.mock to mock heavy external dependencies (Whisper, Sarvam, LLM, ChromaDB).
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.deps import rag_sessions


@pytest.fixture(autouse=True)
def clear_rag_sessions():
    """Ensure clean RAG session state before each test."""
    rag_sessions.clear()
    yield
    rag_sessions.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ── Health Check ───────────────────────────────────────────────────────

def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


# ── Input Validation Tests ─────────────────────────────────────────────

def test_transcribe_invalid_source(client):
    # Empty string or unsupported extension
    response = client.post("/api/v1/transcribe", json={"source": "invalid_file.txt", "engine": "whisper"})
    assert response.status_code == 422


def test_summarize_short_transcript(client):
    # Transcript with fewer than 3 words fails validation schema
    response = client.post("/api/v1/summarize", json={"transcript": "hello world"})
    assert response.status_code == 422


def test_rag_index_blank_fields(client):
    response = client.post(
        "/api/v1/rag/index",
        json={"transcript": "   ", "video_id": "", "video_title": "", "session_id": ""},
    )
    assert response.status_code == 422


def test_rag_query_short_question(client):
    response = client.post(
        "/api/v1/rag/query",
        json={"question": "a", "session_id": "test_session"},
    )
    assert response.status_code == 422


# ── Transcription Endpoint ─────────────────────────────────────────────

@patch("api.routes.transcription.transcribe_all")
@patch("api.routes.transcription.process_input")
def test_transcribe_success(mock_process, mock_transcribe, client):
    mock_process.return_value = ["chunk1.wav", "chunk2.wav"]
    mock_transcribe.return_value = "This is a full transcribed meeting test text."

    response = client.post(
        "/api/v1/transcribe",
        json={"source": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "engine": "whisper"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "This is a full transcribed meeting test text."
    assert data["word_count"] == 8
    assert data["chunks_processed"] == 2
    mock_process.assert_called_once_with("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "whisper")
    mock_transcribe.assert_called_once_with(["chunk1.wav", "chunk2.wav"], "whisper")


# ── Analysis Endpoints ─────────────────────────────────────────────────

@patch("api.routes.analysis.summarize_transcript")
@patch("api.routes.analysis.get_cached_llm")
def test_summarize_endpoint(mock_llm, mock_summarize, client):
    mock_llm.return_value = MagicMock()
    mock_summarize.return_value = "This is the executive meeting summary."

    response = client.post(
        "/api/v1/summarize",
        json={"transcript": "Today we discussed the quarterly product roadmap and deadlines."},
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "This is the executive meeting summary."
    mock_summarize.assert_called_once()


@patch("api.routes.analysis.generate_title")
@patch("api.routes.analysis.get_cached_llm")
def test_title_endpoint(mock_llm, mock_title, client):
    mock_llm.return_value = MagicMock()
    mock_title.return_value = "Q3 Product Planning Meeting"

    response = client.post(
        "/api/v1/title",
        json={"transcript": "Today we discussed the quarterly product roadmap and deadlines."},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Q3 Product Planning Meeting"
    mock_title.assert_called_once()


@patch("api.routes.analysis.extract_action_items")
@patch("api.routes.analysis.get_cached_llm")
def test_extract_action_items_endpoint(mock_llm, mock_extract, client):
    mock_llm.return_value = MagicMock()
    mock_extract.return_value = "1. Finish API documentation - Alice - Friday"

    response = client.post(
        "/api/v1/extract/action-items",
        json={"transcript": "Alice needs to finish the API documentation by Friday."},
    )

    assert response.status_code == 200
    assert response.json()["result"] == "1. Finish API documentation - Alice - Friday"
    mock_extract.assert_called_once()


@patch("api.routes.analysis.extract_key_decisions")
@patch("api.routes.analysis.get_cached_llm")
def test_extract_decisions_endpoint(mock_llm, mock_extract, client):
    mock_llm.return_value = MagicMock()
    mock_extract.return_value = "1. Deploy FastAPI service on port 8000."

    response = client.post(
        "/api/v1/extract/decisions",
        json={"transcript": "We decided to deploy the FastAPI service on port 8000."},
    )

    assert response.status_code == 200
    assert response.json()["result"] == "1. Deploy FastAPI service on port 8000."
    mock_extract.assert_called_once()


@patch("api.routes.analysis.extract_questions")
@patch("api.routes.analysis.get_cached_llm")
def test_extract_questions_endpoint(mock_llm, mock_extract, client):
    mock_llm.return_value = MagicMock()
    mock_extract.return_value = "1. What is the cloud hosting budget?"

    response = client.post(
        "/api/v1/extract/questions",
        json={"transcript": "We still need to confirm what the cloud hosting budget is."},
    )

    assert response.status_code == 200
    assert response.json()["result"] == "1. What is the cloud hosting budget?"
    mock_extract.assert_called_once()


# ── RAG Endpoints ──────────────────────────────────────────────────────

@patch("api.routes.rag.build_rag_chain")
@patch("api.routes.rag.get_cached_llm")
def test_rag_index_endpoint(mock_llm, mock_build, client):
    mock_llm.return_value = MagicMock()
    fake_chain = MagicMock()
    mock_build.return_value = fake_chain

    payload = {
        "transcript": "Alice: We will launch version 1.0 next Monday morning.",
        "video_id": "vid123",
        "video_title": "Launch Prep",
        "session_id": "sess-456",
    }
    response = client.post("/api/v1/rag/index", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "sess-456"
    assert data["video_id"] == "vid123"
    assert "sess-456" in rag_sessions


def test_rag_query_session_not_found(client):
    response = client.post(
        "/api/v1/rag/query",
        json={"question": "When is launch?", "session_id": "nonexistent-sess"},
    )
    assert response.status_code == 404
    assert "No RAG session found" in response.json()["detail"]


@patch("api.routes.rag.ask_question")
def test_rag_query_success(mock_ask, client):
    mock_ask.return_value = "The launch is next Monday morning."
    fake_chain = MagicMock()
    rag_sessions["active-sess"] = fake_chain

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "When is launch?", "session_id": "active-sess"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "The launch is next Monday morning."
    assert data["session_id"] == "active-sess"
    mock_ask.assert_called_once_with(fake_chain, "When is launch?")


# ── Pipeline Endpoint ──────────────────────────────────────────────────

@patch("api.routes.pipeline.os.remove")
@patch("api.routes.pipeline.build_rag_chain")
@patch("api.routes.pipeline.extract_questions")
@patch("api.routes.pipeline.extract_key_decisions")
@patch("api.routes.pipeline.extract_action_items")
@patch("api.routes.pipeline.summarize_transcript")
@patch("api.routes.pipeline.generate_title")
@patch("api.routes.pipeline.transcribe_all")
@patch("api.routes.pipeline.process_input")
@patch("api.routes.pipeline.get_cached_llm")
def test_pipeline_full_run(
    mock_llm,
    mock_process,
    mock_transcribe,
    mock_title,
    mock_summary,
    mock_actions,
    mock_decisions,
    mock_questions,
    mock_build_rag,
    mock_remove,
    client,
):
    mock_llm.return_value = MagicMock()
    mock_process.return_value = ["temp_chunk.wav"]
    mock_transcribe.return_value = "Meeting discussing the release candidate and timelines."
    mock_title.return_value = "Release Candidate Discussion"
    mock_summary.return_value = "Summary of the release candidate discussions."
    mock_actions.return_value = "Action item 1"
    mock_decisions.return_value = "Decision 1"
    mock_questions.return_value = "Question 1"
    mock_build_rag.return_value = MagicMock()

    payload = {
        "source": "https://www.youtube.com/watch?v=test12345",
        "engine": "whisper",
        "session_id": "pipeline-sess-1",
    }
    response = client.post("/api/v1/pipeline", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Release Candidate Discussion"
    assert data["summary"] == "Summary of the release candidate discussions."
    assert data["action_items"] == "Action item 1"
    assert data["key_decisions"] == "Decision 1"
    assert data["open_questions"] == "Question 1"
    assert data["session_id"] == "pipeline-sess-1"
    assert "pipeline-sess-1" in rag_sessions
