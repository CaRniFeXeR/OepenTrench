from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, create_engine

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SQLITE = _REPO_ROOT / "data" / "oepentrench_api.db"


def get_sqlite_path() -> Path:
    """Resolve SQLite file path (override with OEPENTRENCH_SQLITE_PATH)."""
    override = os.environ.get("OEPENTRENCH_SQLITE_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return _DEFAULT_SQLITE.resolve()


_sqlite_path = get_sqlite_path()
_sqlite_path.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{_sqlite_path.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
