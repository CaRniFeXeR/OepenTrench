from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field, SQLModel

from src.api.helpers.time import utc_now


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


class ProjectStatus(str, Enum):
    draft = "draft"
    analysing = "analysing"
    complete = "complete"


class GeojsonStatus(str, Enum):
    missing = "missing"
    ready = "ready"


class PhotoDocumentationCategory(str, Enum):
    """Per-photo documentation quality (map node/segment rollup), not workflow status."""

    green = "green"
    yellow = "yellow"
    red = "red"


class Project(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=64)
    name: str = Field(max_length=500, index=True)
    created_at: datetime
    region: str | None = Field(default=None, max_length=128)
    updated_at: datetime | None = Field(default=None)
    photo_count: int | None = Field(default=None)
    status: ProjectStatus = Field(default=ProjectStatus.draft)
    geojson_status: GeojsonStatus = Field(default=GeojsonStatus.missing)
    project_date: date | None = Field(default=None)


class ProjectAsset(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=64)
    project_id: str = Field(foreign_key="project.id", max_length=64, index=True)
    kind: AssetKind
    original_label: str = Field(max_length=500)
    stored_relpath: str = Field(max_length=1024)
    created_at: datetime


class PhotoAnalysis(SQLModel, table=True):
    """Pipeline / reviewer state for one image asset (1:1 with ProjectAsset when kind is image)."""

    asset_id: str = Field(
        primary_key=True,
        foreign_key="projectasset.id",
        max_length=64,
    )
    is_in_domain: bool = Field(default=False)
    has_white_paper: bool = Field(default=False)
    has_ruler: bool = Field(default=False)
    estimated_depth: float | None = Field(default=None)
    has_duct: bool = Field(default=False)
    estimate_number_of_ducts: int | None = Field(default=None)
    has_gdpr_problems: bool = Field(default=False)
    is_duplicated: bool = Field(default=False)
    category: PhotoDocumentationCategory | None = Field(default=None)
    has_sand_bedding: bool = Field(default=False)
    has_pipe_end_seal: bool = Field(default=False)
    gps_matches_route: bool = Field(default=False)
    date_valid: bool = Field(default=False)
    is_false_call: bool = Field(default=False)
    reviewer_override_category: PhotoDocumentationCategory | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ProjectCreate(SQLModel):
    name: str = Field(max_length=500, min_length=1)
    region: str | None = Field(default=None, max_length=128)
    project_date: date | None = Field(default=None)


class ProjectRead(SQLModel):
    id: str
    name: str
    created_at: datetime
    region: str | None
    updated_at: datetime | None
    photo_count: int | None
    status: ProjectStatus
    geojson_status: GeojsonStatus
    project_date: date | None


class PhotoAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    asset_id: str
    is_in_domain: bool
    has_white_paper: bool
    has_ruler: bool
    estimated_depth: float | None
    has_duct: bool
    estimate_number_of_ducts: int | None
    has_gdpr_problems: bool
    is_duplicated: bool
    category: PhotoDocumentationCategory | None
    has_sand_bedding: bool
    has_pipe_end_seal: bool
    gps_matches_route: bool
    date_valid: bool
    is_false_call: bool
    reviewer_override_category: PhotoDocumentationCategory | None
    created_at: datetime
    updated_at: datetime


class ProjectAssetRead(SQLModel):
    id: str
    project_id: str
    kind: AssetKind
    original_label: str
    stored_relpath: str
    created_at: datetime
    analysis: PhotoAnalysisRead | None = None


class ProjectDetailRead(SQLModel):
    id: str
    name: str
    created_at: datetime
    region: str | None
    updated_at: datetime | None
    photo_count: int | None
    status: ProjectStatus
    geojson_status: GeojsonStatus
    project_date: date | None
    assets: list[ProjectAssetRead]
