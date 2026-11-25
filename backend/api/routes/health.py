"""Health-check route."""

from fastapi import APIRouter
from schemas.responses import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the API status and version.",
)
async def health_check():
    return HealthResponse()
