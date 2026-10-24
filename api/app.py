"""
AI Video Assistant — FastAPI Application

Run:
    uvicorn api.app:app --reload --port 8000

Swagger docs:  http://localhost:8000/docs
ReDoc:         http://localhost:8000/redoc
"""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.routes import health, pipeline, transcription, analysis, rag

# ── App creation ─────────────────────────────────────────────────────

app = FastAPI(
    title="AI Video Assistant API",
    description=(
        "REST API for processing video/audio, transcribing, summarizing, "
        "extracting insights, and conducting RAG-powered Q&A over meeting transcripts."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Global exception handlers ───────────────────────────────────────

@app.exception_handler(ValidationError)
async def pydantic_validation_handler(_request: Request, exc: ValidationError):
    """Convert Pydantic validation errors to a 422 response."""
    errors = []
    for err in exc.errors():
        loc = " → ".join(str(part) for part in err.get("loc", []))
        errors.append(f"{loc}: {err['msg']}")

    return JSONResponse(
        status_code=422,
        content={"detail": "; ".join(errors)},
    )


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    """Catch ValueError raised by business logic (bad inputs, etc.)."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


# ── Register routers under /api/v1 ──────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(pipeline.router, prefix=API_PREFIX)
app.include_router(transcription.router, prefix=API_PREFIX)
app.include_router(analysis.router, prefix=API_PREFIX)
app.include_router(rag.router, prefix=API_PREFIX)


# ── Root redirect ────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "AI Video Assistant API", "docs": "/docs"}
