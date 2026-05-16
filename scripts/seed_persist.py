"""Persist project assets for seeding without triggering the analysis pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import BinaryIO

from sqlmodel import Session, col, select

from src.api.helpers.time import utc_now
from src.api.ids import new_nanoid
from src.api.models import AssetKind, GeojsonStatus, Project, ProjectAsset
from src.api.uploads import (
    ensure_upload_root_exists,
    normalize_geojson_extension,
    normalize_image_extension,
    project_asset_abs_path,
    stored_relpath_for_project_asset,
)

MAX_IMAGE_BYTES = 50 * 1024 * 1024
MAX_GEOJSON_BYTES = 10 * 1024 * 1024

TRENCHES_SUFFIX = "Trenches.geojson"
FCP_POLYGONS_SUFFIX = "FCP_Polygons.geojson"
_REQUIRED_GEOJSON_SUFFIXES = frozenset({TRENCHES_SUFFIX, FCP_POLYGONS_SUFFIX})

_GEOJSON_ROOT_TYPES = frozenset(
    {
        "Feature",
        "FeatureCollection",
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
        "GeometryCollection",
    }
)


def _read_body_limited(stream: BinaryIO, limit: int) -> bytes:
    data = stream.read()
    if len(data) > limit:
        raise ValueError("payload too large")
    return data


def _validate_geojson_document(doc: object) -> None:
    if not isinstance(doc, dict):
        raise ValueError("GeoJSON root must be a JSON object")
    if doc.get("type") not in _GEOJSON_ROOT_TYPES:
        raise ValueError("invalid or missing GeoJSON type")


def validate_geojson_bytes(data: bytes) -> dict:
    doc = json.loads(data.decode("utf-8"))
    _validate_geojson_document(doc)
    return doc


def endswith_geojson_suffix(label: str, suffix: str) -> bool:
    return label.strip().lower().endswith(suffix.lower())


def _geojson_assets(session: Session, project_id: str) -> list[ProjectAsset]:
    statement = (
        select(ProjectAsset)
        .where(ProjectAsset.project_id == project_id)
        .where(ProjectAsset.kind == AssetKind.geojson)
        .order_by(col(ProjectAsset.created_at))
    )
    return list(session.exec(statement).all())


def _recompute_geojson_status(session: Session, project: Project) -> None:
    assets = _geojson_assets(session, project.id)
    has_trenches = any(
        endswith_geojson_suffix(a.original_label, TRENCHES_SUFFIX) for a in assets
    )
    has_fcp = any(
        endswith_geojson_suffix(a.original_label, FCP_POLYGONS_SUFFIX) for a in assets
    )
    project.geojson_status = (
        GeojsonStatus.ready if has_trenches and has_fcp else GeojsonStatus.missing
    )
    project.updated_at = utc_now()
    session.add(project)


def _remove_geojson_with_suffix(session: Session, *, project_id: str, suffix: str) -> None:
    upload_root = ensure_upload_root_exists()
    for asset in _geojson_assets(session, project_id):
        if not endswith_geojson_suffix(asset.original_label, suffix):
            continue
        try:
            path = project_asset_abs_path(
                upload_root=upload_root, stored_relpath=asset.stored_relpath
            )
            if path.is_file():
                path.unlink()
        except ValueError:
            pass
        session.delete(asset)


def _write_asset(
    session: Session,
    *,
    project_id: str,
    kind: AssetKind,
    original_label: str,
    ext: str,
    content: bytes,
) -> ProjectAsset:
    upload_root = ensure_upload_root_exists()
    asset_id = new_nanoid()
    relpath = stored_relpath_for_project_asset(
        project_id=project_id, asset_id=asset_id, ext=ext
    )
    abs_path = upload_root.joinpath(*Path(relpath).parts)
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(content)
    row = ProjectAsset(
        id=asset_id,
        project_id=project_id,
        kind=kind,
        original_label=original_label,
        stored_relpath=relpath.replace("\\", "/"),
        created_at=utc_now(),
    )
    session.add(row)
    return row


def persist_geojson(
    session: Session,
    *,
    project_id: str,
    filename: str,
    content: bytes,
) -> ProjectAsset:
    matched = None
    for suffix in _REQUIRED_GEOJSON_SUFFIXES:
        if endswith_geojson_suffix(filename, suffix):
            matched = suffix
            break
    if matched is None:
        raise ValueError(
            "filename must end with Trenches.geojson or FCP_Polygons.geojson"
        )
    validate_geojson_bytes(content)
    _remove_geojson_with_suffix(session, project_id=project_id, suffix=matched)
    ext = normalize_geojson_extension(filename)
    row = _write_asset(
        session,
        project_id=project_id,
        kind=AssetKind.geojson,
        original_label=filename,
        ext=ext,
        content=content,
    )
    project = session.get(Project, project_id)
    if project is not None:
        _recompute_geojson_status(session, project)
    session.commit()
    session.refresh(row)
    return row


def persist_image(
    session: Session,
    *,
    project_id: str,
    filename: str,
    content: bytes,
) -> ProjectAsset:
    ext = normalize_image_extension(filename)
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("payload too large")
    row = _write_asset(
        session,
        project_id=project_id,
        kind=AssetKind.image,
        original_label=filename,
        ext=ext,
        content=content,
    )
    session.commit()
    session.refresh(row)
    return row


def persist_geojson_file(
    session: Session, *, project_id: str, path: Path
) -> ProjectAsset:
    return persist_geojson(
        session,
        project_id=project_id,
        filename=path.name,
        content=path.read_bytes(),
    )


def persist_image_file(
    session: Session,
    *,
    project_id: str,
    label: str,
    image_path: Path,
) -> ProjectAsset:
    return persist_image(
        session,
        project_id=project_id,
        filename=label,
        content=image_path.read_bytes(),
    )
