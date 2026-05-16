from __future__ import annotations

from sqlmodel import Session

from src.api.helpers.geojson_sampling import random_point_in_geojson_bounds
from src.api.helpers.photo_documentation_category import (
    REVIEWER_CLEAR_ATTRS,
    automated_category,
)
from src.api.helpers.time import utc_now
from src.api.models import (
    AssetKind,
    GeojsonStatus,
    GpsCoordinates,
    PhotoAnalysis,
    PhotoAnalysisReviewUpdate,
    PhotoDocumentationCategory,
    Project,
    ProjectAsset,
)
from src.api.services.extract_img_metadata_service import extract_img_metadata
from src.api.services.project_asset_service import load_merged_project_geojson


def _dummy_analysis_fields() -> dict:
    return {
        "is_in_domain": True,
        "has_white_paper": True,
        "has_ruler": True,
        "estimated_depth": 1.2,
        "has_duct": True,
        "estimate_number_of_ducts": 1,
        "has_gdpr_problems": False,
        "is_duplicated": False,
        "gps_matches_route": True,
        "date_valid": True,
        "is_false_call": False,
    }


def _resolve_gps_coordinates(
    session: Session,
    *,
    project: Project,
    extracted: GpsCoordinates | None,
) -> dict | None:
    if "dummy" in project.name.lower():
        if project.geojson_status != GeojsonStatus.ready:
            return None
        geojson = load_merged_project_geojson(session, project.id)
        return random_point_in_geojson_bounds(geojson)
    return extracted.model_dump(mode="json") if extracted is not None else None


def _validate_image_asset(
    session: Session,
    *,
    project_id: str,
    asset_id: str,
) -> tuple[ProjectAsset, Project]:
    project = session.get(Project, project_id)
    if project is None:
        raise LookupError("project not found")
    asset = session.get(ProjectAsset, asset_id)
    if asset is None:
        raise LookupError("asset not found")
    if asset.project_id != project_id:
        raise ValueError("asset does not belong to project")
    if asset.kind != AssetKind.image:
        raise ValueError("asset is not an image")
    return asset, project


def _clear_reviewer_state(row: PhotoAnalysis) -> None:
    for attr in REVIEWER_CLEAR_ATTRS:
        setattr(row, attr, None)


def analyze_image_asset(
    session: Session,
    *,
    project_id: str,
    asset_id: str,
) -> PhotoAnalysis:
    _asset, project = _validate_image_asset(
        session, project_id=project_id, asset_id=asset_id
    )
    extracted = extract_img_metadata(
        session, project_id=project_id, asset_id=asset_id
    )
    fields = _dummy_analysis_fields()
    fields["gps_coordinates"] = _resolve_gps_coordinates(
        session, project=project, extracted=extracted
    )
    row = _upsert_analysis(session, asset_id=asset_id, fields=fields, reanalyze=True)
    row.category = automated_category(row)
    session.add(row)
    return row


def analyze_image_asset_by_id(session: Session, asset_id: str) -> PhotoAnalysis:
    asset = session.get(ProjectAsset, asset_id)
    if asset is None:
        raise LookupError("asset not found")
    return analyze_image_asset(
        session,
        project_id=asset.project_id,
        asset_id=asset_id,
    )


def review_image_analysis(
    session: Session,
    *,
    project_id: str,
    asset_id: str,
    payload: PhotoAnalysisReviewUpdate,
) -> PhotoAnalysis:
    _validate_image_asset(session, project_id=project_id, asset_id=asset_id)
    existing = session.get(PhotoAnalysis, asset_id)
    if existing is None:
        raise LookupError("analysis not found")

    updates = payload.model_dump(exclude_unset=True)
    mark_reviewed = updates.pop("mark_reviewed", True)

    for key, value in updates.items():
        setattr(existing, key, value)

    if mark_reviewed:
        existing.reviewed_at = utc_now()

    existing.updated_at = utc_now()
    session.add(existing)
    return existing


def _upsert_analysis(
    session: Session,
    *,
    asset_id: str,
    fields: dict,
    reanalyze: bool = False,
) -> PhotoAnalysis:
    now = utc_now()
    existing = session.get(PhotoAnalysis, asset_id)
    if existing is not None:
        if reanalyze:
            _clear_reviewer_state(existing)
        for key, value in fields.items():
            setattr(existing, key, value)
        existing.updated_at = now
        session.add(existing)
        return existing

    row = PhotoAnalysis(
        asset_id=asset_id,
        created_at=now,
        updated_at=now,
        category=PhotoDocumentationCategory.yellow,
        **fields,
    )
    session.add(row)
    return row
