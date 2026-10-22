from typing import Optional
from pydantic import BaseModel, Field, field_validator


class IndexTranscriptRequest(BaseModel):
    transcript: str = Field(..., description="Transcript text to index")
    video_id: str = Field(..., description="Unique video identifier")
    video_title: str = Field(..., description="Video or meeting title")
    session_id: str = Field(..., description="Active session ID")

    @field_validator("transcript", "video_id", "video_title", "session_id")
    @classmethod
    def not_blank(cls, v: str, info) -> str:
        v = v.strip()
        if not v:
            raise ValueError(f"{info.field_name} cannot be empty or whitespace.")
        return v


class QueryRequest(BaseModel):
    question: str = Field(..., description="Question to ask about the meeting")
    session_id: Optional[str] = None
    selected_video_id: Optional[str] = None
    k: int = Field(default=4, ge=1, le=20, description="Number of context chunks to retrieve")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Question must be at least 2 characters long.")
        return v
