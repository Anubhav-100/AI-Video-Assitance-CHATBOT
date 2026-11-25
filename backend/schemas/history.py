"""Pydantic schemas for analysis history endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HistoryCreateRequest(BaseModel):
    title: str = Field(..., description="Meeting or video title")
    source: str = Field(default="", description="Original video URL or file path")
    session_id: str = Field(..., description="RAG session identifier")
    video_id: Optional[str] = Field(default=None, description="Video identifier")
    transcript: str = Field(..., description="Full transcribed text")
    summary: str = Field(..., description="Generated summary")
    action_items: str = Field(default="", description="Extracted action items")
    key_decisions: str = Field(default="", description="Extracted key decisions")
    open_questions: str = Field(default="", description="Extracted open questions")
    engine: str = Field(default="whisper", description="Transcription engine used")

    @field_validator("title", "session_id", "transcript", "summary")
    @classmethod
    def not_blank(cls, v: str, info) -> str:
        v = v.strip()
        if not v:
            raise ValueError(f"{info.field_name} cannot be empty or whitespace.")
        return v


class HistorySummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source: str
    session_id: str
    video_id: Optional[str] = None
    summary: str
    engine: str
    created_at: datetime
    updated_at: datetime


class HistoryDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source: str
    session_id: str
    video_id: Optional[str] = None
    transcript: str
    summary: str
    action_items: str
    key_decisions: str
    open_questions: str
    engine: str
    created_at: datetime
    updated_at: datetime


class HistoryDeleteResponse(BaseModel):
    id: int
    deleted: bool = True
    message: str = "Analysis deleted successfully"
