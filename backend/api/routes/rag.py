"""RAG routes — index a transcript and query it."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from schemas.rag import IndexTranscriptRequest, QueryRequest
from schemas.responses import RagIndexResponse, RagQueryResponse, ErrorResponse
from api.deps import get_cached_llm, get_or_restore_rag_chain, rag_sessions
from db.database import get_db

from core.rag_engine import build_rag_chain, ask_question

router = APIRouter(prefix="/rag", tags=["RAG"])


# ── Index ────────────────────────────────────────────────────────────

@router.post(
    "/index",
    response_model=RagIndexResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Index a transcript for RAG Q&A",
    description=(
        "Splits the transcript, embeds it into the vector store, "
        "and creates a RAG chain for the given session."
    ),
)
async def index_transcript(body: IndexTranscriptRequest):
    try:
        llm = get_cached_llm()

        rag_chain = build_rag_chain(
            llm=llm,
            transcript=body.transcript,
            video_id=body.video_id,
            video_title=body.video_title,
            session_id=body.session_id,
        )

        rag_sessions[body.session_id] = rag_chain

        return RagIndexResponse(
            session_id=body.session_id,
            video_id=body.video_id,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Query ────────────────────────────────────────────────────────────

@router.post(
    "/query",
    response_model=RagQueryResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Ask a question about an indexed transcript",
    description=(
        "Queries the RAG chain for the given session_id. "
        "The transcript must have been indexed first via /rag/index or /pipeline."
    ),
)
async def query_transcript(body: QueryRequest, db: Session = Depends(get_db)):
    session_id = body.session_id
    try:
        rag_chain = get_or_restore_rag_chain(session_id, db=db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if rag_chain is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No RAG session found for session_id='{session_id}'. "
                "Index a transcript first via POST /api/v1/rag/index or /api/v1/pipeline."
            ),
        )

    try:
        answer = ask_question(rag_chain, body.question)

        return RagQueryResponse(answer=answer, session_id=session_id)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
