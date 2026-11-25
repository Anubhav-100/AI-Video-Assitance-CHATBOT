"""SQLAlchemy ORM models for persistent analysis history."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisHistory(Base):
    """Persisted record of a completed video/audio analysis."""

    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    session_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    video_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    action_items: Mapped[str] = mapped_column(Text, nullable=False, default="")
    key_decisions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    open_questions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    engine: Mapped[str] = mapped_column(String(64), nullable=False, default="whisper")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )
