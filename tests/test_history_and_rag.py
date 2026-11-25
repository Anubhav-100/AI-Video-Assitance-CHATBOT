"""Tests for SQLite analysis history, pipeline auto-save, RAG restart persistence, and frontend client."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.embeddings import Embeddings

from api.app import app
from api.deps import rag_sessions
from core.vector_store import build_vector_store, has_session_vectors


class DeterministicFakeEmbeddings(Embeddings):
    """Lightweight offline embeddings for testing ChromaDB persistence without model downloads."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t) % 10), 1.0, 0.5, 0.25] for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text) % 10), 1.0, 0.5, 0.25]


@pytest.fixture
def client():
    rag_sessions.clear()
    with TestClient(app) as test_client:
        yield test_client
    rag_sessions.clear()


# ── History CRUD Endpoints ─────────────────────────────────────────────

def test_history_crud_and_newest_first_ordering(client):
    payload_1 = {
        "title": "First Meeting",
        "source": "https://example.com/video1",
        "session_id": "sess-1",
        "video_id": "vid-1",
        "transcript": "Alice: Let us review the Q1 roadmap.",
        "summary": "Reviewed Q1 roadmap.",
        "action_items": "- Alice to share slides",
        "key_decisions": "- Ship beta on Friday",
        "open_questions": "- Who owns QA?",
        "engine": "whisper",
    }
    payload_2 = {
        "title": "Second Meeting",
        "source": "meeting.mp4",
        "session_id": "sess-2",
        "video_id": "meeting",
        "transcript": "Bob: Budget is approved for Q2.",
        "summary": "Approved Q2 budget.",
        "action_items": "- Bob to notify finance",
        "key_decisions": "- Budget approved",
        "open_questions": "",
        "engine": "sarvam",
    }

    r1 = client.post("/api/v1/history", json=payload_1)
    assert r1.status_code == 201
    id1 = r1.json()["id"]

    r2 = client.post("/api/v1/history", json=payload_2)
    assert r2.status_code == 201
    id2 = r2.json()["id"]

    # List should be newest first
    lst = client.get("/api/v1/history")
    assert lst.status_code == 200
    items = lst.json()
    assert [item["id"] for item in items] == [id2, id1]
    assert items[0]["title"] == "Second Meeting"
    assert items[0]["engine"] == "sarvam"

    # Retrieve complete analysis
    detail = client.get(f"/api/v1/history/{id1}")
    assert detail.status_code == 200
    d = detail.json()
    assert d["transcript"] == payload_1["transcript"]
    assert d["action_items"] == payload_1["action_items"]
    assert d["key_decisions"] == payload_1["key_decisions"]
    assert d["open_questions"] == payload_1["open_questions"]

    # Delete analysis
    deleted = client.delete(f"/api/v1/history/{id1}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    # Deleted item returns 404
    assert client.get(f"/api/v1/history/{id1}").status_code == 404
    assert client.delete(f"/api/v1/history/{id1}").status_code == 404


# ── Pipeline Auto-Save Behavior ────────────────────────────────────────

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
def test_pipeline_auto_saves_on_success(
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
    mock_process.return_value = ["chunk.wav"]
    mock_transcribe.return_value = "Team discussed database persistence and RAG."
    mock_title.return_value = "Persistence Architecture Sync"
    mock_summary.return_value = "Agreed on SQLite + ChromaDB."
    mock_actions.return_value = "Implement history endpoints"
    mock_decisions.return_value = "Use SQLAlchemy"
    mock_questions.return_value = "Any migration needed?"
    mock_build_rag.return_value = MagicMock()

    resp = client.post(
        "/api/v1/pipeline",
        json={
            "source": "https://www.youtube.com/watch?v=abc123",
            "engine": "whisper",
            "session_id": "auto-save-sess",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Persistence Architecture Sync"
    assert data["session_id"] == "auto-save-sess"

    history = client.get("/api/v1/history").json()
    assert len(history) == 1
    assert history[0]["session_id"] == "auto-save-sess"
    assert history[0]["source"] == "https://www.youtube.com/watch?v=abc123"
    assert history[0]["engine"] == "whisper"


@patch("api.routes.pipeline.process_input", side_effect=RuntimeError("Download failed"))
def test_pipeline_does_not_save_on_failure(mock_process, client):
    resp = client.post(
        "/api/v1/pipeline",
        json={"source": "https://www.youtube.com/watch?v=fail", "engine": "whisper"},
    )
    assert resp.status_code == 500
    history = client.get("/api/v1/history").json()
    assert history == []


# ── RAG Persistence Across Restart ─────────────────────────────────────

def test_rag_query_restores_from_persistent_chromadb_without_reembedding(
    client, tmp_path, monkeypatch
):
    chroma_dir = tmp_path / "chroma_test_db"
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(chroma_dir))

    fake_embeddings = DeterministicFakeEmbeddings()
    with patch("core.vector_store.get_embeddings", return_value=fake_embeddings):
        build_vector_store(
            transcript="Alice confirmed the product launch is scheduled for November 15.",
            video_id="vid-persist",
            video_title="Launch Sync",
            session_id="restart-sess-1",
        )
        assert has_session_vectors("restart-sess-1") is True

        # Simulate FastAPI restart: in-memory rag_sessions is completely empty
        rag_sessions.clear()

        with patch("api.deps.get_cached_llm", return_value=MagicMock()), \
             patch("api.deps.build_rag_chain") as mock_build, \
             patch("api.routes.rag.ask_question", return_value="November 15") as mock_ask:
            resp = client.post(
                "/api/v1/rag/query",
                json={"session_id": "restart-sess-1", "question": "When is the launch?"},
            )

        assert resp.status_code == 200
        assert resp.json()["answer"] == "November 15"
        assert "restart-sess-1" in rag_sessions
        mock_build.assert_not_called()
        mock_ask.assert_called_once()


# ── Frontend API Client Tests ──────────────────────────────────────────

def test_frontend_api_client_history_helpers():
    frontend_dir = str(Path(__file__).resolve().parents[1] / "frontend")
    if frontend_dir not in sys.path:
        sys.path.insert(0, frontend_dir)

    import api_client

    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"id": 1, "title": "Saved"}]
    mock_resp.raise_for_status.return_value = None

    with patch("api_client.requests.get", return_value=mock_resp) as mock_get:
        res = api_client.list_analysis_history()
        assert res == [{"id": 1, "title": "Saved"}]
        mock_get.assert_called_once()

    mock_resp.json.return_value = {"id": 1, "title": "Saved"}
    with patch("api_client.requests.get", return_value=mock_resp) as mock_get:
        res = api_client.get_analysis_history(1)
        assert res["id"] == 1
        mock_get.assert_called_once()

    with patch("api_client.requests.post", return_value=mock_resp) as mock_post:
        res = api_client.save_analysis_history({"title": "Saved"})
        assert res["id"] == 1
        mock_post.assert_called_once()

    mock_resp.json.return_value = {"id": 1, "deleted": True}
    with patch("api_client.requests.delete", return_value=mock_resp) as mock_del:
        res = api_client.delete_analysis_history(1)
        assert res["deleted"] is True
        mock_del.assert_called_once()
