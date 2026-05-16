from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.health import router as health_router
from src.api.routes.items import router as items_router
from src.api.routes.projects import router as projects_router

logger = logging.getLogger("oepentrench.api")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _configure_logging() -> None:
    log_dir = _repo_root() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "api.log"

    logger.setLevel(logging.INFO)
    if logger.handlers:
        return

    handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    logger.addHandler(handler)


def _upgrade_db() -> None:
    repo_root = _repo_root()
    alembic_cfg = Config(str(repo_root / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("API starting")
    _upgrade_db()
    logger.info("Database migrations applied")
    yield
    logger.info("API shutting down")


_configure_logging()
logger.info("API module loaded")

app = FastAPI(title="OepenTrench API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(items_router)
app.include_router(projects_router)
