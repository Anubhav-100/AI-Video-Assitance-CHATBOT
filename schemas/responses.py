"""Lightweight response schemas for API endpoints.

These complement the existing schemas in schemas/ without duplicating them.
"""

from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"


class TranscriptResponse(BaseModel):
    transcript: str = Field(..., description="Full transcribed text")
    word_count: int = Field(..., description="Number of words in the transcript")
    chunks_processed: int = Field(..., description="Number of audio chunks processed")


class TitleResponse(BaseModel):
    title: str = Field(..., description="Generated meeting title")


class SummaryResponse(BaseModel):
    summary: str = Field(..., description="Generated meeting summary")


class ExtractionResponse(BaseModel):
    result: str = Field(..., description="Extracted items as formatted text")


class RagIndexResponse(BaseModel):
    session_id: str = Field(..., description="Session ID for this RAG index")
    video_id: str = Field(..., description="Video identifier")
    message: str = "Transcript indexed successfully"


class RagQueryResponse(BaseModel):
    answer: str = Field(..., description="LLM-generated answer from transcript context")
    session_id: str = Field(..., description="Session ID used for the query")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human-readable error message")
