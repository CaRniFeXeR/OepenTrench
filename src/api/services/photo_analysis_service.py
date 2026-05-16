from __future__ import annotations

from sqlmodel import Session

from src.api.helpers.geojson_sampling import random_point_in_geojson_bounds
from src.api.helpers.time import utc_now
from src.api.models import (
    AssetKind,
    GeojsonStatus,
    PhotoAnalysis,
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
        "category": PhotoDocumentationCategory.green,
        "gps_matches_route": True,
        "date_valid": True,
        "is_false_call": False,
        "reviewer_override_category": None,
    }


def _resolve_gps_coordinates(
    session: Session,
    *,
    project: Project,
    metadata: dict,
) -> dict | None:
    if "dummy" in project.name.lower():
        if project.geojson_status != GeojsonStatus.ready:
            return None
        geojson = load_merged_project_geojson(session, project.id)
        return random_point_in_geojson_bounds(geojson)
    return metadata.get("gps_coordinates")


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


def analyze_image_asset(
    session: Session,
    *,
    project_id: str,
    asset_id: str,
) -> PhotoAnalysis:
    _asset, project = _validate_image_asset(
        session, project_id=project_id, asset_id=asset_id
    )
    metadata = extract_img_metadata(
        session, project_id=project_id, asset_id=asset_id
    )
    fields = _dummy_analysis_fields()
    fields["gps_coordinates"] = _resolve_gps_coordinates(
        session, project=project, metadata=metadata
    )
    return _upsert_analysis(session, asset_id=asset_id, fields=fields)


def analyze_image_asset_by_id(session: Session, asset_id: str) -> PhotoAnalysis:
    asset = session.get(ProjectAsset, asset_id)
    if asset is None:
        raise LookupError("asset not found")
    return analyze_image_asset(
        session,
        project_id=asset.project_id,
        asset_id=asset_id,
    )


def _upsert_analysis(
    session: Session, *, asset_id: str, fields: dict
) -> PhotoAnalysis:
    now = utc_now()
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
