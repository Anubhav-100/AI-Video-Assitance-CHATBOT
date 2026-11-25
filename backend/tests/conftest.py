"""Shared pytest fixtures ensuring tests never touch real user databases."""

import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db.database import configure_database, init_db  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_test_database(tmp_path):
    """Point SQLAlchemy to a fresh temporary SQLite database for every test."""
    db_path = tmp_path / "test_history.db"
    eng = configure_database(f"sqlite:///{db_path.as_posix()}")
    init_db()
    yield db_path
    eng.dispose()
