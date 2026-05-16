from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.api.models.common import PhotoDocumentationCategory


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


class ProjectCoverageSummaryRead(BaseModel):
    compartment_count: int
    covered_count: int
    coverage_ratio: float
    fcp_count: int
    computed_at: datetime | None


class FcpCoverageRead(BaseModel):
    project: ProjectCoverageSummaryRead
    compartments: list[FcpCoverageCompartmentRead]
    summaries: list[FcpCoverageSummaryRead]
