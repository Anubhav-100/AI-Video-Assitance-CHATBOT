from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

from schemas.audio import VALID_EXTENSIONS


class PipelineInput(BaseModel):
    source: str = Field(..., description="YouTube URL or local media file path")
    engine: Literal["whisper", "sarvam"] = "whisper"
    session_id: Optional[str] = None
    video_id: Optional[str] = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Source cannot be empty.")
        is_url = v.startswith("http://") or v.startswith("https://")
        is_media = v.lower().endswith(VALID_EXTENSIONS)
        if not (is_url or is_media):
            raise ValueError("Source must be a web URL or a supported audio/video file.")
        return v

    @field_validator("engine", mode="before")
    @classmethod
    def normalize_engine(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v
