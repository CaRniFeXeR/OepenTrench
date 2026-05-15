from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class Item(SQLModel, table=True):
    """Example table; all SQLModel tables live in this module."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=500, index=True)
    created_at: datetime


class ItemCreate(SQLModel):
    name: str = Field(max_length=500, min_length=1)


class ItemRead(SQLModel):
    id: int
    name: str
    created_at: datetime


class AssetKind(str, Enum):
    image = "image"
    geojson = "geojson"


class Project(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=64)
    name: str = Field(max_length=500, index=True)
    created_at: datetime


class ProjectAsset(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=64)
    project_id: str = Field(foreign_key="project.id", max_length=64, index=True)
    kind: AssetKind
    original_label: str = Field(max_length=500)
    stored_relpath: str = Field(max_length=1024)
    created_at: datetime


class ProjectCreate(SQLModel):
    name: str = Field(max_length=500, min_length=1)


class ProjectRead(SQLModel):
    id: str
    name: str
    created_at: datetime


class ProjectAssetRead(SQLModel):
    id: str
    project_id: str
    kind: AssetKind
    original_label: str
    stored_relpath: str
    created_at: datetime


class ProjectDetailRead(SQLModel):
    id: str
    name: str
    created_at: datetime
    assets: list[ProjectAssetRead]
