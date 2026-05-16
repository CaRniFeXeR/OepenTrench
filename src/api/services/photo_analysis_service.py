from __future__ import annotations

from sqlmodel import Session

from src.api.helpers.time import utc_now
from src.api.models import (
    AssetKind,
    PhotoAnalysis,
    PhotoDocumentationCategory,
    Project,
    ProjectAsset,
)

_DUMMY_GPS_COORDINATES = {
    "type": "Point",
    "coordinates": [14.2958, 46.5537],
}


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
        "category": PhotoDocumentationCategory.green,
        "has_sand_bedding": True,
        "has_pipe_end_seal": True,
        "gps_matches_route": True,
        "date_valid": True,
        "is_false_call": False,
        "reviewer_override_category": None,
        "gps_coordinates": _DUMMY_GPS_COORDINATES,
    }


def _validate_image_asset(
    session: Session,
    *,
    project_id: str,
    asset_id: str,
) -> ProjectAsset:
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
    return asset


def analyze_image_asset(
    session: Session,
    *,
    project_id: str,
    asset_id: str,
) -> PhotoAnalysis:
    _validate_image_asset(session, project_id=project_id, asset_id=asset_id)
    return _upsert_dummy_analysis(session, asset_id=asset_id)


def analyze_image_asset_by_id(session: Session, asset_id: str) -> PhotoAnalysis:
    asset = session.get(ProjectAsset, asset_id)
    if asset is None:
        raise LookupError("asset not found")
    return analyze_image_asset(
        session,
        project_id=asset.project_id,
        asset_id=asset_id,
    )


def _upsert_dummy_analysis(session: Session, *, asset_id: str) -> PhotoAnalysis:
    now = utc_now()
    fields = _dummy_analysis_fields()
    existing = session.get(PhotoAnalysis, asset_id)
    if existing is not None:
        for key, value in fields.items():
            setattr(existing, key, value)
        existing.updated_at = now
        session.add(existing)
        return existing

    row = PhotoAnalysis(
        asset_id=asset_id,
        created_at=now,
        updated_at=now,
        **fields,
    )
    session.add(row)
    return row
