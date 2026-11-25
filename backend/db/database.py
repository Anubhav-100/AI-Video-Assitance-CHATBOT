"""SQLite database configuration and session management using SQLAlchemy."""

import os
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = BACKEND_DIR / "data"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "history.db"


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


def get_database_url() -> str:
    """Resolve the database URL from environment variables or default persistent path."""
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    db_path_str = os.getenv("HISTORY_DB_PATH")
    db_path = Path(db_path_str) if db_path_str else DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


def _create_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


engine: Engine = _create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def configure_database(database_url: Optional[str] = None) -> Engine:
    """Reconfigure the SQLAlchemy engine and session factory (useful for tests)."""
    global engine
    url = database_url or get_database_url()
    if url.startswith("sqlite:///"):
        sqlite_path = Path(url.replace("sqlite:///", "", 1))
        if str(sqlite_path) != ":memory:":
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    engine.dispose()
    engine = _create_engine(url)
    SessionLocal.configure(bind=engine)
    return engine


def init_db() -> None:
    """Create all database tables if they do not exist."""
    import db.models  # noqa: F401 - ensure models are registered on Base.metadata

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
