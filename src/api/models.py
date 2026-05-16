from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from src.api.helpers.time import utc_now


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
    """Per-photo documentation quality (map node/segment rollup), not workflow status.

    Rules and review workflow: docs/photo-documentation-category.md
    """

    green = "green"
    yellow = "yellow"
    red = "red"


class GpsCoordinates(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]  # [longitude, latitude]


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
    hash_sha256: str = Field(max_length=64)
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
    gps_matches_route: bool = Field(default=False)
    date_valid: bool = Field(default=False)
    is_false_call: bool = Field(default=False)
    reviewer_override_category: PhotoDocumentationCategory | None = Field(default=None)
    reviewer_has_duct: bool | None = Field(default=None)
    reviewer_has_ruler: bool | None = Field(default=None)
    reviewer_is_in_domain: bool | None = Field(default=None)
    reviewer_has_gdpr_problems: bool | None = Field(default=None)
    reviewer_gps_matches_route: bool | None = Field(default=None)
    reviewed_at: datetime | None = Field(default=None)
    gps_coordinates: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ProjectCreate(SQLModel):
    name: str = Field(max_length=500, min_length=1)
    region: str | None = Field(default=None, max_length=128)
    project_date: date | None = Field(default=None)


class ProjectUpdate(SQLModel):
    name: str = Field(max_length=500, min_length=1)


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
    model_config = ConfigDict(use_enum_values=True)

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
    gps_matches_route: bool
    date_valid: bool
    is_false_call: bool
    reviewer_override_category: PhotoDocumentationCategory | None
    reviewer_has_duct: bool | None
    reviewer_has_ruler: bool | None
    reviewer_is_in_domain: bool | None
    reviewer_has_gdpr_problems: bool | None
    reviewer_gps_matches_route: bool | None
    reviewed_at: datetime | None
    gps_coordinates: GpsCoordinates | None
    created_at: datetime
    updated_at: datetime
    effective_has_duct: bool
    effective_has_ruler: bool
    effective_is_in_domain: bool
    effective_has_gdpr_problems: bool
    effective_gps_matches_route: bool
    effective_category: PhotoDocumentationCategory | None


class PhotoAnalysisReviewUpdate(BaseModel):
    reviewer_has_duct: bool | None = None
    reviewer_has_ruler: bool | None = None
    reviewer_is_in_domain: bool | None = None
    reviewer_has_gdpr_problems: bool | None = None
    reviewer_gps_matches_route: bool | None = None
    reviewer_override_category: PhotoDocumentationCategory | None = None
    mark_reviewed: bool = True


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


class MapPhotoMarkerRead(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    asset_id: str
    coordinates: tuple[float, float]
    category: PhotoDocumentationCategory | None
    fcp_id: str | None
    fcp_code: str | None
    fcp_label: str | None


class MapPhotosRead(BaseModel):
    photos: list[MapPhotoMarkerRead]


class FcpCoverageCompartmentRead(BaseModel):
    id: str
    fcp_id: str
    covered: bool
    length_m: float
    center: tuple[float, float]
    geometry: dict


class FcpCoverageSummaryRead(BaseModel):
    fcp_id: str
    fcp_code: str | None
    fcp_label: str | None
    compartment_count: int
    covered_count: int
    coverage_ratio: float


class FcpCoverageRead(BaseModel):
    compartments: list[FcpCoverageCompartmentRead]
    summaries: list[FcpCoverageSummaryRead]
