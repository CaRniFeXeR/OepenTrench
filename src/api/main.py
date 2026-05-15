from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.health import router as health_router
from src.api.routes.items import router as items_router
from src.api.routes.projects import router as projects_router


def _upgrade_db() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    alembic_cfg = Config(str(repo_root / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _upgrade_db()
    yield


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
