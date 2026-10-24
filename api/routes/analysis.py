"""Analysis routes — summarize, title, and extraction endpoints."""

from fastapi import APIRouter, HTTPException

from schemas.analysis import SummarizeRequest
from schemas.responses import SummaryResponse, TitleResponse, ExtractionResponse, ErrorResponse
from api.deps import get_cached_llm

from core.summarizer import summarize_transcript, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions

router = APIRouter(tags=["Analysis"])


# ── Summarize ────────────────────────────────────────────────────────

@router.post(
    "/summarize",
    response_model=SummaryResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Summarize a transcript",
    description="Generates a professional meeting summary from the provided transcript text.",
)
async def summarize(body: SummarizeRequest):
    try:
        llm = get_cached_llm()
        summary = summarize_transcript(body.transcript, llm)
        return SummaryResponse(summary=summary)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Title ────────────────────────────────────────────────────────────

@router.post(
    "/title",
    response_model=TitleResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Generate a title for a transcript",
    description="Produces a concise, professional meeting title (max 8 words) from the transcript.",
)
async def title(body: SummarizeRequest):
    try:
        llm = get_cached_llm()
        result = generate_title(body.transcript, llm)
        return TitleResponse(title=result)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Extract Action Items ─────────────────────────────────────────────

@router.post(
    "/extract/action-items",
    response_model=ExtractionResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Extract action items from a transcript",
)
async def action_items(body: SummarizeRequest):
    try:
        llm = get_cached_llm()
        result = extract_action_items(body.transcript, llm)
        return ExtractionResponse(result=result)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Extract Key Decisions ────────────────────────────────────────────

@router.post(
    "/extract/decisions",
    response_model=ExtractionResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Extract key decisions from a transcript",
)
async def decisions(body: SummarizeRequest):
    try:
        llm = get_cached_llm()
        result = extract_key_decisions(body.transcript, llm)
        return ExtractionResponse(result=result)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Extract Open Questions ───────────────────────────────────────────

@router.post(
    "/extract/questions",
    response_model=ExtractionResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Extract open questions from a transcript",
)
async def questions(body: SummarizeRequest):
    try:
        llm = get_cached_llm()
        result = extract_questions(body.transcript, llm)
        return ExtractionResponse(result=result)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
