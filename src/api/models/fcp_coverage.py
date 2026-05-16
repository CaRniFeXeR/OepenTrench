from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from src.api.helpers.time import utc_now


class ProjectFcpCoverage(SQLModel, table=True):
    project_id: str = Field(
        primary_key=True,
        foreign_key="project.id",
        max_length=64,
    )
    computed_at: datetime = Field(default_factory=utc_now)


class FcpCoverageSummary(SQLModel, table=True):
    project_id: str = Field(
        foreign_key="project.id",
        max_length=64,
        primary_key=True,
    )
    fcp_id: str = Field(max_length=128, primary_key=True)
    fcp_code: str | None = Field(default=None, max_length=128)
    fcp_label: str | None = Field(default=None, max_length=500)
    compartment_count: int = Field(default=0)
    covered_count: int = Field(default=0)
    coverage_ratio: float = Field(default=0.0)


class FcpCoverageCompartment(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=256)
    project_id: str = Field(foreign_key="project.id", max_length=64, index=True)
    fcp_id: str = Field(max_length=128, index=True)
    covered: bool = Field(default=False)
    length_m: float = Field(default=0.0)
    center: dict = Field(sa_column=Column(JSON))
    geometry: dict = Field(sa_column=Column(JSON))
