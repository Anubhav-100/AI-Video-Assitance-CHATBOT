from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SummarizeRequest(BaseModel):
    transcript: str = Field(..., description="Transcript text to summarize")

    @field_validator("transcript")
    @classmethod
    def validate_transcript(cls, v: str) -> str:
        v = v.strip()
        if len(v.split()) < 3:
            raise ValueError("Transcript must contain at least 3 words to analyze.")
        return v


class MeetingAnalysisResult(BaseModel):
    title: str = Field(..., description="Meeting title (concise summary)")
    transcript: str = Field(..., description="Full transcribed text")
    summary: str = Field(..., description="Generated meeting summary")
    action_items: str = Field(default="", description="Extracted action items")
    key_decisions: str = Field(default="", description="Extracted key decisions")
    open_questions: str = Field(default="", description="Extracted open questions")
    video_id: Optional[str] = None
    session_id: Optional[str] = None

    @field_validator("title", "summary")
    @classmethod
    def not_blank(cls, v: str, info) -> str:
        v = v.strip()
        if not v:
            raise ValueError(f"{info.field_name} cannot be empty or whitespace.")
        return v
