from __future__ import annotations

import json
from pathlib import Path
from typing import BinaryIO, Optional

from sqlmodel import Session

from src.api.helpers.time import utc_now
from src.api.ids import new_nanoid
from src.api.models import AssetKind, Project, ProjectAsset
from src.api.uploads import (
    ensure_upload_root_exists,
    normalize_geojson_extension,
    normalize_image_extension,
    stored_relpath_for_project_asset,
)

MAX_IMAGE_BYTES = 50 * 1024 * 1024
MAX_GEOJSON_BYTES = 10 * 1024 * 1024

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


def _validate_geojson_document(doc: object) -> None:
    if not isinstance(doc, dict):
        raise ValueError("GeoJSON root must be a JSON object")
    t = doc.get("type")
    if t not in _GEOJSON_ROOT_TYPES:
        raise ValueError("invalid or missing GeoJSON type")


def validate_geojson_bytes(data: bytes) -> None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("GeoJSON must be UTF-8") from exc
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON") from exc
    _validate_geojson_document(doc)


def _read_body_limited(stream: BinaryIO, limit: int) -> bytes:
    data = stream.read()
    if len(data) > limit:
        raise PayloadTooLarge(limit)
    return data


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
    ext = normalize_geojson_extension(upload_filename)
    content = _read_body_limited(stream, MAX_GEOJSON_BYTES)
    validate_geojson_bytes(content)
    return _persist_asset(
        session,
        project_id=project_id,
        kind=AssetKind.geojson,
        original_label=original_label,
        ext=ext,
        content=content,
    )


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
        session.commit()
        session.refresh(row)
        return row
    except Exception:
        session.rollback()
        if written_path is not None and written_path.is_file():
            written_path.unlink(missing_ok=True)
        raise
