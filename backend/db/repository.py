"""Repository functions for AnalysisHistory CRUD operations."""

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import AnalysisHistory


def create_analysis(
    db: Session,
    *,
    title: str,
    source: str,
    session_id: str,
    video_id: Optional[str],
    transcript: str,
    summary: str,
    action_items: str = "",
    key_decisions: str = "",
    open_questions: str = "",
    engine: str = "whisper",
) -> AnalysisHistory:
    """Persist a new analysis history record and return it."""
    record = AnalysisHistory(
        title=title,
        source=source,
        session_id=session_id,
        video_id=video_id,
        transcript=transcript,
        summary=summary,
        action_items=action_items,
        key_decisions=key_decisions,
        open_questions=open_questions,
        engine=engine,
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except SQLAlchemyError:
        db.rollback()
        raise


def list_analyses(
    db: Session,
    *,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[AnalysisHistory]:
    """Return saved analyses ordered newest first."""
    stmt = (
        select(AnalysisHistory)
        .order_by(AnalysisHistory.created_at.desc(), AnalysisHistory.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def get_analysis_by_id(db: Session, analysis_id: int) -> Optional[AnalysisHistory]:
    """Return a single analysis by its primary key ID."""
    return db.get(AnalysisHistory, analysis_id)


def get_analysis_by_session_id(db: Session, session_id: str) -> Optional[AnalysisHistory]:
    """Return the newest analysis matching the given session_id."""
    stmt = (
        select(AnalysisHistory)
        .where(AnalysisHistory.session_id == session_id)
        .order_by(AnalysisHistory.created_at.desc(), AnalysisHistory.id.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def delete_analysis(db: Session, analysis_id: int) -> bool:
    """Delete an analysis by ID. Returns True if deleted, False if not found."""
    record = db.get(AnalysisHistory, analysis_id)
    if record is None:
        return False
    try:
        db.delete(record)
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
