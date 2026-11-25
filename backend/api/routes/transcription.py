"""Transcription route."""

from fastapi import APIRouter, HTTPException

from schemas.audio import AudioProcessRequest
from schemas.responses import TranscriptResponse, ErrorResponse
from core.audio_processor import process_input
from core.transcriber import transcribe_all

router = APIRouter(tags=["Transcription"])


@router.post(
    "/transcribe",
    response_model=TranscriptResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Transcribe audio from a URL or local file",
    description=(
        "Downloads/converts the source, chunks the audio, "
        "and transcribes using the selected engine (whisper or sarvam)."
    ),
)
async def transcribe(body: AudioProcessRequest):
    try:
        chunks = process_input(body.source, body.engine)
        transcript = transcribe_all(chunks, body.engine)

        return TranscriptResponse(
            transcript=transcript,
            word_count=len(transcript.split()),
            chunks_processed=len(chunks),
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
