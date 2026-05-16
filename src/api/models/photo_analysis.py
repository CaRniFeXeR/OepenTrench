from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from src.api.helpers.time import utc_now
from src.api.models.common import GpsCoordinates, PhotoDocumentationCategory


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
    reviewer_is_duplicated: bool | None = Field(default=None)
    reviewed_at: datetime | None = Field(default=None)
    gps_coordinates: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


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
    reviewer_is_duplicated: bool | None
    reviewed_at: datetime | None
    gps_coordinates: GpsCoordinates | None
    created_at: datetime
    updated_at: datetime
    effective_has_duct: bool
    effective_has_ruler: bool
    effective_is_in_domain: bool
    effective_has_gdpr_problems: bool
    effective_gps_matches_route: bool
    effective_is_duplicated: bool
    effective_category: PhotoDocumentationCategory | None


class PhotoAnalysisReviewUpdate(BaseModel):
    reviewer_has_duct: bool | None = None
    reviewer_has_ruler: bool | None = None
    reviewer_is_in_domain: bool | None = None
    reviewer_has_gdpr_problems: bool | None = None
    reviewer_gps_matches_route: bool | None = None
    reviewer_is_duplicated: bool | None = None
    reviewer_override_category: PhotoDocumentationCategory | None = None
    mark_reviewed: bool = True
