from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from sqlmodel import Session, col, select

from src.api.database import engine
from src.api.helpers.time import utc_now
from src.api.models import OnlineLearningTrainingRun, OnlineLearningTrainingStatus
from src.api.routes.health import router as health_router
from src.api.routes.online_learning import router as online_learning_router
from src.api.routes.projects import router as projects_router

logger = logging.getLogger("oepentrench.api")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _configure_logging() -> None:
    log_dir = _repo_root() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "api.log"

    pkg_logger = logging.getLogger("oepentrench")
    pkg_logger.setLevel(logging.INFO)
    if pkg_logger.handlers:
        return

    handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    pkg_logger.addHandler(handler)
    pkg_logger.propagate = False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"
        client = request.client.host if request.client else "-"
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "%s %s 500 %.1fms client=%s",
                request.method,
                path,
                duration_ms,
                client,
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s %s %.1fms client=%s",
            request.method,
            path,
            response.status_code,
            duration_ms,
            client,
        )
        return response


def _upgrade_db() -> None:
    repo_root = _repo_root()
    alembic_cfg = Config(str(repo_root / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def _fail_stale_training_runs() -> None:
    with Session(engine) as session:
        rows = session.exec(
            select(OnlineLearningTrainingRun).where(
                col(OnlineLearningTrainingRun.status) == OnlineLearningTrainingStatus.running,
            )
        ).all()
        if not rows:
            return
        now = utc_now()
        for row in rows:
            row.status = OnlineLearningTrainingStatus.failed
            row.finished_at = now
            if row.started_at.tzinfo is None:
                started = row.started_at.replace(tzinfo=now.tzinfo)
            else:
                started = row.started_at
            row.duration_sec = max(0, int((now - started).total_seconds()))
            row.error_message = "interrupted by server restart"
            session.add(row)
        session.commit()
        logger.info("marked %d stale training run(s) as failed", len(rows))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("API starting")
    _upgrade_db()
    logger.info("Database migrations applied")
    _fail_stale_training_runs()
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
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(online_learning_router)
