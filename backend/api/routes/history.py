"""History routes — save, list, retrieve, and delete persistent analyses."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.database import get_db
from db.repository import (
    create_analysis,
    delete_analysis,
    get_analysis_by_id,
    list_analyses,
)
from schemas.history import (
    HistoryCreateRequest,
    HistoryDeleteResponse,
    HistoryDetailResponse,
    HistorySummaryItem,
)
from schemas.responses import ErrorResponse

router = APIRouter(prefix="/history", tags=["History"])


@router.post(
    "",
    response_model=HistoryDetailResponse,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Save a completed analysis to persistent history",
)
async def save_history(
    body: HistoryCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        record = create_analysis(
            db,
            title=body.title,
            source=body.source,
            session_id=body.session_id,
            video_id=body.video_id,
            transcript=body.transcript,
            summary=body.summary,
            action_items=body.action_items,
            key_decisions=body.key_decisions,
            open_questions=body.open_questions,
            engine=body.engine,
        )
        return record
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while saving analysis: {exc}",
        ) from exc


@router.get(
    "",
    response_model=list[HistorySummaryItem],
    responses={500: {"model": ErrorResponse}},
    summary="List saved analyses (newest first)",
)
async def get_history_list(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    try:
        return list_analyses(db, limit=limit, offset=offset)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while listing history: {exc}",
        ) from exc


@router.get(
    "/{analysis_id}",
    response_model=HistoryDetailResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Retrieve a complete saved analysis by ID",
)
async def get_history_detail(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    try:
        record = get_analysis_by_id(db, analysis_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while retrieving analysis: {exc}",
        ) from exc

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis with id={analysis_id} was not found.",
        )
    return record


@router.delete(
    "/{analysis_id}",
    response_model=HistoryDeleteResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Delete a saved analysis by ID",
)
async def delete_history_item(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    try:
        deleted = delete_analysis(db, analysis_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while deleting analysis: {exc}",
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis with id={analysis_id} was not found.",
        )
    return HistoryDeleteResponse(id=analysis_id)
