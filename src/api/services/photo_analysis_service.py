from __future__ import annotations

import logging
import time
from typing import Any

from sqlmodel import Session, select

from src.api.helpers.face_detection import image_path_has_detected_face
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
from src.api.uploads import get_upload_root, project_asset_abs_path

logger = logging.getLogger("oepentrench.api.photo_analysis")

SENTINEL_HASH_SHA256 = "0" * 64


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
        "gps_matches_route": False,
        "date_valid": True,
        "is_false_call": False,
    }


def _gps_summary(gps: dict | None) -> str:
    if gps is None:
        return "none"
    coords = gps.get("coordinates")
    if not isinstance(coords, (list, tuple)) or len(coords) < 2:
        return f"invalid_coords={coords!r}"
    try:
        lon = float(coords[0])
        lat = float(coords[1])
    except (TypeError, ValueError):
        return f"invalid_coords={coords!r}"
    return f"lon={lon:.6f},lat={lat:.6f}"


def _resolve_gps_coordinates(
    session: Session,
    *,
    project: Project,
    extracted: GpsCoordinates | None,
    asset_id: str,
) -> dict | None:
    is_dummy_project = "dummy" in project.name.lower()
    if is_dummy_project:
        if project.geojson_status != GeojsonStatus.ready:
            logger.info(
                "gps_resolve asset_id=%s source=dummy_random skipped geojson_status=%s",
                asset_id,
                project.geojson_status,
            )
            return None
        geojson = load_merged_project_geojson(session, project.id)
        point = random_point_in_geojson_bounds(geojson)
        logger.info(
            "gps_resolve asset_id=%s source=dummy_random %s",
            asset_id,
            _gps_summary(point),
        )
        return point

    if extracted is not None:
        gps = extracted.model_dump(mode="json")
        logger.info(
            "gps_resolve asset_id=%s source=extracted %s",
            asset_id,
            _gps_summary(gps),
        )
        return gps

    logger.info("gps_resolve asset_id=%s source=extracted none", asset_id)
    return None


def _is_duplicate_image(
    session: Session,
    *,
    project_id: str,
    asset: ProjectAsset,
) -> bool:
    if asset.hash_sha256 == SENTINEL_HASH_SHA256:
        return False
    stmt = (
        select(ProjectAsset)
        .where(
            ProjectAsset.project_id == project_id,
            ProjectAsset.kind == AssetKind.image,
            ProjectAsset.hash_sha256 == asset.hash_sha256,
            ProjectAsset.id != asset.id,
            ProjectAsset.created_at < asset.created_at,
        )
        .limit(1)
    )
    return session.exec(stmt).first() is not None


def _validate_image_asset(
    session: Session,
    *,
    project_id: str,
    asset_id: str,
) -> tuple[ProjectAsset, Project]:
    project = session.get(Project, project_id)
    if project is None:
        logger.warning(
            "validate_image_asset failed project_id=%s asset_id=%s reason=project_not_found",
            project_id,
            asset_id,
        )
        raise LookupError("project not found")
    asset = session.get(ProjectAsset, asset_id)
    if asset is None:
        logger.warning(
            "validate_image_asset failed project_id=%s asset_id=%s reason=asset_not_found",
            project_id,
            asset_id,
        )
        raise LookupError("asset not found")
    if asset.project_id != project_id:
        logger.warning(
            "validate_image_asset failed project_id=%s asset_id=%s reason=asset_project_mismatch actual_project_id=%s",
            project_id,
            asset_id,
            asset.project_id,
        )
        raise ValueError("asset does not belong to project")
    if asset.kind != AssetKind.image:
        logger.warning(
            "validate_image_asset failed project_id=%s asset_id=%s reason=not_image kind=%s",
            project_id,
            asset_id,
            asset.kind,
        )
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
    started = time.perf_counter()
    logger.info(
        "analyze_start project_id=%s asset_id=%s",
        project_id,
        asset_id,
    )

    asset, project = _validate_image_asset(
        session, project_id=project_id, asset_id=asset_id
    )
    logger.info(
        "analyze_validated project_id=%s asset_id=%s project_name=%r geojson_status=%s stored_relpath=%s",
        project_id,
        asset_id,
        project.name,
        project.geojson_status,
        asset.stored_relpath,
    )

    upload_root = get_upload_root()
    image_path = project_asset_abs_path(
        upload_root=upload_root, stored_relpath=asset.stored_relpath
    )
    logger.info(
        "analyze_image_path project_id=%s asset_id=%s path=%s exists=%s",
        project_id,
        asset_id,
        image_path,
        image_path.is_file(),
    )

    fields = _dummy_analysis_fields()
    fields["is_duplicated"] = _is_duplicate_image(
        session, project_id=project_id, asset=asset
    )
    if not image_path.is_file():
        logger.warning(
            "analyze_image_missing project_id=%s asset_id=%s path=%s using_dummy_fields_only",
            project_id,
            asset_id,
            image_path,
        )
    else:
        # Stage 1: trench gate. If not a trench, hard-zero the in-domain flags
        # and skip the YOLO detector entirely.
        from src.api.services.trench_classifier_service import is_trench

        if is_trench(image_path):
            fields["is_in_domain"] = True
            # Stage 2: YOLO presence check for duct / ruler / whitepaper.
            from src.api.services.yolo_detection_service import detect_target_classes

            fields.update(detect_target_classes(image_path))
        else:
            fields["is_in_domain"] = False
            fields["has_duct"] = False
            fields["has_ruler"] = False
            fields["has_white_paper"] = False

        face_started = time.perf_counter()
        try:
            fields["has_gdpr_problems"] = image_path_has_detected_face(image_path)
        except Exception:
            logger.exception(
                "analyze_face_detection_failed project_id=%s asset_id=%s path=%s",
                project_id,
                asset_id,
                image_path,
            )
            raise
        face_ms = (time.perf_counter() - face_started) * 1000
        logger.info(
            "analyze_face_detection project_id=%s asset_id=%s has_gdpr_problems=%s duration_ms=%.1f",
            project_id,
            asset_id,
            fields["has_gdpr_problems"],
            face_ms,
        )

        metadata_started = time.perf_counter()
        try:
            extracted = extract_img_metadata(image_path)
        except Exception:
            logger.exception(
                "analyze_metadata_extraction_failed project_id=%s asset_id=%s path=%s",
                project_id,
                asset_id,
                image_path,
            )
            raise
        metadata_ms = (time.perf_counter() - metadata_started) * 1000
        logger.info(
            "analyze_metadata_extraction project_id=%s asset_id=%s gps_found=%s duration_ms=%.1f",
            project_id,
            asset_id,
            extracted is not None,
            metadata_ms,
        )

        gps_coordinates = _resolve_gps_coordinates(
            session,
            project=project,
            extracted=extracted,
            asset_id=asset_id,
        )
        fields["gps_coordinates"] = gps_coordinates

        if gps_coordinates is not None:
            coords = gps_coordinates.get("coordinates")
            if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                try:
                    lon = float(coords[0])
                    lat = float(coords[1])
                    if project.geojson_status == GeojsonStatus.ready:
                        from src.api.services.compartment_service import (
                            photo_matches_route,
                        )

                        route_started = time.perf_counter()
                        fields["gps_matches_route"] = photo_matches_route(
                            session, project.id, lon, lat
                        )
                        route_ms = (time.perf_counter() - route_started) * 1000
                        logger.info(
                            "analyze_route_match project_id=%s asset_id=%s lon=%.6f lat=%.6f gps_matches_route=%s duration_ms=%.1f",
                            project_id,
                            asset_id,
                            lon,
                            lat,
                            fields["gps_matches_route"],
                            route_ms,
                        )
                    else:
                        logger.info(
                            "analyze_route_match_skipped project_id=%s asset_id=%s geojson_status=%s",
                            project_id,
                            asset_id,
                            project.geojson_status,
                        )
                except (TypeError, ValueError) as exc:
                    logger.warning(
                        "analyze_route_match_invalid_coords project_id=%s asset_id=%s coords=%r error=%s",
                        project_id,
                        asset_id,
                        coords,
                        exc,
                    )
            else:
                logger.warning(
                    "analyze_route_match_missing_coords project_id=%s asset_id=%s gps=%r",
                    project_id,
                    asset_id,
                    gps_coordinates,
                )

    row = _upsert_analysis(
        session,
        asset_id=asset_id,
        fields=fields,
        reanalyze=True,
        project_id=project_id,
    )
    row.category = automated_category(row)
    session.add(row)

    total_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "analyze_complete project_id=%s asset_id=%s category=%s has_gdpr_problems=%s gps_matches_route=%s gps=%s duration_ms=%.1f",
        project_id,
        asset_id,
        row.category,
        row.has_gdpr_problems,
        row.gps_matches_route,
        _gps_summary(row.gps_coordinates),
        total_ms,
    )
    return row


def analyze_image_asset_by_id(session: Session, asset_id: str) -> PhotoAnalysis:
    logger.info("analyze_by_id_start asset_id=%s", asset_id)
    asset = session.get(ProjectAsset, asset_id)
    if asset is None:
        logger.warning("analyze_by_id_failed asset_id=%s reason=asset_not_found", asset_id)
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
    logger.info(
        "review_start project_id=%s asset_id=%s",
        project_id,
        asset_id,
    )
    _validate_image_asset(session, project_id=project_id, asset_id=asset_id)
    existing = session.get(PhotoAnalysis, asset_id)
    if existing is None:
        logger.warning(
            "review_failed project_id=%s asset_id=%s reason=analysis_not_found",
            project_id,
            asset_id,
        )
        raise LookupError("analysis not found")

    updates = payload.model_dump(exclude_unset=True)
    mark_reviewed = updates.pop("mark_reviewed", True)
    logger.info(
        "review_apply project_id=%s asset_id=%s fields=%s mark_reviewed=%s",
        project_id,
        asset_id,
        sorted(updates.keys()),
        mark_reviewed,
    )

    for key, value in updates.items():
        setattr(existing, key, value)

    if mark_reviewed:
        existing.reviewed_at = utc_now()

    existing.updated_at = utc_now()
    session.add(existing)
    logger.info(
        "review_complete project_id=%s asset_id=%s reviewed_at=%s",
        project_id,
        asset_id,
        existing.reviewed_at,
    )
    return existing


def _upsert_analysis(
    session: Session,
    *,
    asset_id: str,
    fields: dict[str, Any],
    reanalyze: bool = False,
    project_id: str | None = None,
) -> PhotoAnalysis:
    now = utc_now()
    existing = session.get(PhotoAnalysis, asset_id)
    if existing is not None:
        action = "update"
        if reanalyze:
            _clear_reviewer_state(existing)
            logger.info(
                "upsert_cleared_reviewer_state asset_id=%s project_id=%s attrs=%s",
                asset_id,
                project_id,
                REVIEWER_CLEAR_ATTRS,
            )
        for key, value in fields.items():
            setattr(existing, key, value)
        existing.updated_at = now
        session.add(existing)
    else:
        action = "insert"
        row = PhotoAnalysis(
            asset_id=asset_id,
            created_at=now,
            updated_at=now,
            category=PhotoDocumentationCategory.yellow,
            **fields,
        )
        session.add(row)
        existing = row

    logger.info(
        "upsert_analysis asset_id=%s project_id=%s action=%s field_keys=%s",
        asset_id,
        project_id,
        action,
        sorted(fields.keys()),
    )
    return existing
