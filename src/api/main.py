from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel

from src.api.database import engine
from src.api.routes.health import router as health_router
from src.api.routes.items import router as items_router
from src.api.routes.projects import router as projects_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(title="OepenTrench API", lifespan=lifespan)
app.include_router(health_router)
app.include_router(items_router)
app.include_router(projects_router)
