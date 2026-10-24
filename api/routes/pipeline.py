"""Full pipeline route — audio → transcript → analysis → RAG index."""

import os
import uuid

from fastapi import APIRouter, HTTPException

from schemas.pipeline import PipelineInput
from schemas.analysis import MeetingAnalysisResult
from schemas.responses import ErrorResponse
from api.deps import get_cached_llm, rag_sessions

from core.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize_transcript, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain

router = APIRouter(tags=["Pipeline"])


@router.post(
    "/pipeline",
    response_model=MeetingAnalysisResult,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Run the full processing pipeline",
    description=(
        "Accepts a video URL or local file path, processes audio, transcribes, "
        "generates title & summary, extracts action items / decisions / questions, "
        "and builds a RAG index for follow-up Q&A."
    ),
)
async def run_full_pipeline(body: PipelineInput):
    try:
        source = body.source
        engine = body.engine

        # 1. Process audio
        chunks = process_input(source, engine)

        # 2. Transcribe
        transcript = transcribe_all(chunks, engine)

        # 3. Init LLM
        llm = get_cached_llm()

        # 4. Title + Summary
        title = generate_title(transcript, llm)
        summary = summarize_transcript(transcript, llm)

        # 5. Extraction
        action_items = extract_action_items(transcript, llm)
        key_decisions = extract_key_decisions(transcript, llm)
        open_questions = extract_questions(transcript, llm)

        # 6. RAG index
        video_id = (
            os.path.splitext(os.path.basename(source))[0]
            if not source.startswith("http")
            else uuid.uuid4().hex[:8]
        )
        session_id = body.session_id or uuid.uuid4().hex[:12]

        rag_chain = build_rag_chain(
            llm=llm,
            transcript=transcript,
            video_id=video_id,
            video_title=title,
            session_id=session_id,
        )

        # Store for later queries
        rag_sessions[session_id] = rag_chain

        # Cleanup temp chunks
        for c in chunks:
            try:
                os.remove(c)
            except OSError:
                pass

        return MeetingAnalysisResult(
            title=title,
            transcript=transcript,
            summary=summary,
            action_items=action_items,
            key_decisions=key_decisions,
            open_questions=open_questions,
            video_id=video_id,
            session_id=session_id,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
