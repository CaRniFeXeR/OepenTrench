from __future__ import annotations

from src.api.models.common import AssetKind, GpsCoordinates, PhotoDocumentationCategory
from src.api.models.fcp_coverage import (
    FcpCoverageCompartment,
    FcpCoverageSummary,
    ProjectFcpCoverage,
)
from src.api.models.map import (
    FcpCoverageCompartmentRead,
    FcpCoverageRead,
    FcpCoverageSummaryRead,
    MapPhotoMarkerRead,
    MapPhotosRead,
    ProjectCoverageSummaryRead,
)
from src.api.models.online_learning import (
    OnlineLearningDisagreementsPage,
    OnlineLearningMismatchItemRead,
    OnlineLearningStatsRead,
    OnlineLearningTrainingRun,
    OnlineLearningTrainingRunRead,
    OnlineLearningTrainingRunsPage,
    OnlineLearningTrainingStatus,
)
from src.api.models.photo_analysis import (
    PhotoAnalysis,
    PhotoAnalysisRead,
    PhotoAnalysisReviewUpdate,
)
from src.api.models.project import (
    GeojsonStatus,
    Project,
    ProjectAsset,
    ProjectAssetRead,
    ProjectCreate,
    ProjectDetailRead,
    ProjectRead,
    ProjectStatus,
    ProjectUpdate,
)

__all__ = [
    "AssetKind",
    "FcpCoverageCompartment",
    "FcpCoverageCompartmentRead",
    "FcpCoverageRead",
    "FcpCoverageSummary",
    "FcpCoverageSummaryRead",
    "ProjectCoverageSummaryRead",
    "ProjectFcpCoverage",
    "GeojsonStatus",
    "GpsCoordinates",
    "MapPhotoMarkerRead",
    "MapPhotosRead",
    "OnlineLearningDisagreementsPage",
    "OnlineLearningMismatchItemRead",
    "OnlineLearningStatsRead",
    "OnlineLearningTrainingRun",
    "OnlineLearningTrainingRunRead",
    "OnlineLearningTrainingRunsPage",
    "OnlineLearningTrainingStatus",
    "PhotoAnalysis",
    "PhotoAnalysisRead",
    "PhotoAnalysisReviewUpdate",
    "PhotoDocumentationCategory",
    "Project",
    "ProjectAsset",
    "ProjectAssetRead",
    "ProjectCreate",
    "ProjectDetailRead",
    "ProjectRead",
    "ProjectStatus",
    "ProjectUpdate",
]
