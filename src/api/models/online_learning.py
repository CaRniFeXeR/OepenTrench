from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field, SQLModel

from src.api.models.photo_analysis import PhotoAnalysisRead


class OnlineLearningStatsRead(BaseModel):
    total_reviewed: int
    total_mismatch: int
    mismatch_rate: float
    projects_with_mismatch: int


class OnlineLearningMismatchItemRead(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    asset_id: str
    project_id: str
    project_name: str
    original_label: str
    created_at: datetime
    reviewed_at: datetime
    analysis: PhotoAnalysisRead
    mismatch_fields: list[str]


class OnlineLearningDisagreementsPage(BaseModel):
    items: list[OnlineLearningMismatchItemRead]
    total: int
    limit: int
    offset: int
    stats: OnlineLearningStatsRead


class OnlineLearningTrainingStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class OnlineLearningTrainingRun(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=64)
    status: OnlineLearningTrainingStatus = Field(
        default=OnlineLearningTrainingStatus.pending,
    )
    photo_count: int = Field(default=0)
    started_at: datetime
    finished_at: datetime | None = Field(default=None)
    duration_sec: int | None = Field(default=None)
    error_message: str | None = Field(default=None, max_length=2048)
    log_relpath: str = Field(max_length=256)


class OnlineLearningTrainingRunRead(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    status: OnlineLearningTrainingStatus
    photo_count: int
    started_at: datetime
    finished_at: datetime | None
    duration_sec: int | None
    error_message: str | None


class OnlineLearningTrainingRunsPage(BaseModel):
    items: list[OnlineLearningTrainingRunRead]
    total: int
    limit: int
    offset: int
