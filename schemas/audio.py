from typing import Literal, List
from pydantic import BaseModel, Field, field_validator

VALID_EXTENSIONS = (
    ".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm",
    ".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg",
)


class AudioProcessRequest(BaseModel):
    source: str = Field(..., description="Video URL or local media file path")
    engine: Literal["whisper", "sarvam"] = "whisper"

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Source cannot be empty.")
        is_url = v.startswith("http://") or v.startswith("https://")
        is_media = v.lower().endswith(VALID_EXTENSIONS)
        if not (is_url or is_media):
            raise ValueError(
                f"Source must be a web URL (http/https) or a supported media file ({', '.join(VALID_EXTENSIONS[:5])}, etc.)."
            )
        return v

    @field_validator("engine", mode="before")
    @classmethod
    def normalize_engine(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class TranscribeRequest(BaseModel):
    chunks: List[str] = Field(..., min_length=1, description="List of audio chunk file paths")
    engine: Literal["whisper", "sarvam"] = "whisper"

    @field_validator("chunks")
    @classmethod
    def validate_chunks(cls, chunks: List[str]) -> List[str]:
        cleaned = [c.strip() for c in chunks if c.strip()]
        if not cleaned:
            raise ValueError("Chunks list cannot be empty.")
        for chunk in cleaned:
            if not chunk.lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
                raise ValueError(f"Chunk '{chunk}' must be a supported audio file (.wav, .mp3, etc.).")
        return cleaned

    @field_validator("engine", mode="before")
    @classmethod
    def normalize_engine(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v
