from __future__ import annotations

import json
from pathlib import Path
from typing import BinaryIO, Optional

from sqlmodel import Session, col, select

from src.api.helpers.time import utc_now
from src.api.ids import new_nanoid
from src.api.models import AssetKind, GeojsonStatus, Project, ProjectAsset
from src.api.services import photo_analysis_service
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


class PayloadTooLarge(Exception):
    def __init__(self, max_bytes: int):
        super().__init__("payload too large")
        self.max_bytes = max_bytes


def endswith_geojson_suffix(label: str, suffix: str) -> bool:
    return label.strip().lower().endswith(suffix.lower())


def required_geojson_suffix_for_label(label: str) -> str | None:
    for suffix in _REQUIRED_GEOJSON_SUFFIXES:
        if endswith_geojson_suffix(label, suffix):
            return suffix
    return None


def geojson_assets_for_project(session: Session, project_id: str) -> list[ProjectAsset]:
    statement = (
        select(ProjectAsset)
        .where(ProjectAsset.project_id == project_id)
        .where(ProjectAsset.kind == AssetKind.geojson)
        .order_by(col(ProjectAsset.created_at))
    )
    return list(session.exec(statement).all())


def project_has_required_geojson(assets: list[ProjectAsset]) -> bool:
    has_trenches = False
    has_fcp_polys = False
    for asset in assets:
        label = asset.original_label
        if endswith_geojson_suffix(label, TRENCHES_SUFFIX):
            has_trenches = True
        if endswith_geojson_suffix(label, FCP_POLYGONS_SUFFIX):
            has_fcp_polys = True
    return has_trenches and has_fcp_polys


def recompute_geojson_status(session: Session, project: Project) -> GeojsonStatus:
    assets = geojson_assets_for_project(session, project.id)
    status = (
        GeojsonStatus.ready
        if project_has_required_geojson(assets)
        else GeojsonStatus.missing
    )
    project.geojson_status = status
    project.updated_at = utc_now()
    session.add(project)
    session.commit()
    session.refresh(project)
    return status


def _validate_geojson_document(doc: object) -> None:
    if not isinstance(doc, dict):
        raise ValueError("GeoJSON root must be a JSON object")
    t = doc.get("type")
    if t not in _GEOJSON_ROOT_TYPES:
        raise ValueError("invalid or missing GeoJSON type")


def validate_geojson_bytes(data: bytes) -> dict:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("GeoJSON must be UTF-8") from exc
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON") from exc
    _validate_geojson_document(doc)
    return doc


def _read_body_limited(stream: BinaryIO, limit: int) -> bytes:
    data = stream.read()
    if len(data) > limit:
        raise PayloadTooLarge(limit)
    return data


def _delete_geojson_asset(session: Session, asset: ProjectAsset) -> None:
    upload_root = ensure_upload_root_exists()
    try:
        abs_path = project_asset_abs_path(
            upload_root=upload_root,
            stored_relpath=asset.stored_relpath,
        )
        if abs_path.is_file():
            abs_path.unlink()
    except ValueError:
        pass
    session.delete(asset)
    session.commit()


def _remove_geojson_assets_with_suffix(
    session: Session,
    *,
    project_id: str,
    suffix: str,
) -> None:
    for asset in geojson_assets_for_project(session, project_id):
        if endswith_geojson_suffix(asset.original_label, suffix):
            _delete_geojson_asset(session, asset)


def _document_to_features(doc: dict) -> list[dict]:
    doc_type = doc.get("type")
    if doc_type == "FeatureCollection":
        raw = doc.get("features")
        return list(raw) if isinstance(raw, list) else []
    if doc_type == "Feature":
        return [doc]
    return [{"type": "Feature", "geometry": doc, "properties": None}]


def merge_geojson_documents(docs: list[dict]) -> dict:
    features: list[dict] = []
    for doc in docs:
        features.extend(_document_to_features(doc))
    return {"type": "FeatureCollection", "features": features}


def _geojson_asset_for_suffix(
    assets: list[ProjectAsset], suffix: str
) -> ProjectAsset | None:
    matches = [a for a in assets if endswith_geojson_suffix(a.original_label, suffix)]
    if not matches:
        return None
    return matches[-1]


def load_merged_project_geojson(session: Session, project_id: str) -> dict:
    project = session.get(Project, project_id)
    if project is None:
        raise LookupError("project not found")
    if project.geojson_status != GeojsonStatus.ready:
        raise ValueError("required GeoJSON files are not ready")

    assets = geojson_assets_for_project(session, project_id)
    trenches_asset = _geojson_asset_for_suffix(assets, TRENCHES_SUFFIX)
    fcp_asset = _geojson_asset_for_suffix(assets, FCP_POLYGONS_SUFFIX)
    if trenches_asset is None or fcp_asset is None:
        raise ValueError("required GeoJSON files are missing")

    upload_root = ensure_upload_root_exists()
    docs: list[dict] = []
    for asset in (trenches_asset, fcp_asset):
        abs_path = project_asset_abs_path(
            upload_root=upload_root,
            stored_relpath=asset.stored_relpath,
        )
        if not abs_path.is_file():
            raise ValueError(f"GeoJSON file missing on disk: {asset.original_label}")
        docs.append(validate_geojson_bytes(abs_path.read_bytes()))

    return merge_geojson_documents(docs)


def save_project_image(
    session: Session,
    *,
    project_id: str,
    upload_filename: str,
    original_label: str,
    stream: BinaryIO,
) -> ProjectAsset:
    project = session.get(Project, project_id)
    if project is None:
        raise LookupError("project not found")
    ext = normalize_image_extension(upload_filename)
    content = _read_body_limited(stream, MAX_IMAGE_BYTES)
    return _persist_asset(
        session,
        project_id=project_id,
        kind=AssetKind.image,
        original_label=original_label,
        ext=ext,
        content=content,
    )


def save_project_geojson(
    session: Session,
    *,
    project_id: str,
    upload_filename: str,
    original_label: str,
    stream: BinaryIO,
) -> ProjectAsset:
    project = session.get(Project, project_id)
    if project is None:
        raise LookupError("project not found")

    matched_suffix = required_geojson_suffix_for_label(original_label)
    if matched_suffix is None:
        raise ValueError(
            "filename must end with Trenches.geojson or FCP_Polygons.geojson"
        )

    ext = normalize_geojson_extension(upload_filename)
    content = _read_body_limited(stream, MAX_GEOJSON_BYTES)
    validate_geojson_bytes(content)

    _remove_geojson_assets_with_suffix(
        session,
        project_id=project_id,
        suffix=matched_suffix,
    )

    row = _persist_asset(
        session,
        project_id=project_id,
        kind=AssetKind.geojson,
        original_label=original_label,
        ext=ext,
        content=content,
    )
    recompute_geojson_status(session, project)
    return row


def _persist_asset(
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
    relpath = stored_relpath_for_project_asset(project_id=project_id, asset_id=asset_id, ext=ext)
    abs_path = upload_root.joinpath(*Path(relpath).parts)

    written_path: Optional[Path] = None
    try:
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(content)
        written_path = abs_path
        row = ProjectAsset(
            id=asset_id,
            project_id=project_id,
            kind=kind,
            original_label=original_label,
            stored_relpath=relpath.replace("\\", "/"),
            created_at=utc_now(),
        )
        session.add(row)
        if kind == AssetKind.image:
            photo_analysis_service.analyze_image_asset(
                session,
                project_id=project_id,
                asset_id=asset_id,
            )
        session.commit()
        session.refresh(row)
        return row
    except Exception:
        session.rollback()
        if written_path is not None and written_path.is_file():
            written_path.unlink(missing_ok=True)
        raise
