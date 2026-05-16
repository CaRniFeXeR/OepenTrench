from __future__ import annotations

import re

from shapely.geometry import Point, shape
from sqlmodel import Session, col, select

from src.api.helpers.photo_documentation_category import effective_category
from src.api.models import (
    AssetKind,
    MapPhotoMarkerRead,
    PhotoAnalysis,
    Project,
    ProjectAsset,
)
from src.api.services.project_asset_service import (
    FCP_POLYGONS_SUFFIX,
    _geojson_asset_for_suffix,
    geojson_assets_for_project,
    validate_geojson_bytes,
)
from src.api.uploads import ensure_upload_root_exists, project_asset_abs_path

_FCP_CODE_RE = re.compile(r"^(\S+)")


def _fcp_code_from_label(label: str | None) -> str | None:
    if not label:
        return None
    match = _FCP_CODE_RE.match(label.strip())
    return match.group(1) if match else None


def _fcp_id_from_properties(props: dict | None) -> str | None:
    if not props:
        return None
    as_oop = props.get("asOop")
    if as_oop is not None:
        return str(as_oop)
    return None


def _load_fcp_polygon_features(session: Session, project_id: str) -> list[dict]:
    assets = geojson_assets_for_project(session, project_id)
    fcp_asset = _geojson_asset_for_suffix(assets, FCP_POLYGONS_SUFFIX)
    if fcp_asset is None:
        return []

    upload_root = ensure_upload_root_exists()
    abs_path = project_asset_abs_path(
        upload_root=upload_root,
        stored_relpath=fcp_asset.stored_relpath,
    )
    if not abs_path.is_file():
        return []

    doc = validate_geojson_bytes(abs_path.read_bytes())
    doc_type = doc.get("type")
    if doc_type == "FeatureCollection":
        raw = doc.get("features")
        return [f for f in raw if isinstance(f, dict)] if isinstance(raw, list) else []
    if doc_type == "Feature":
        return [doc]
    return []


def _assign_fcp(
    lon: float,
    lat: float,
    fcp_features: list[dict],
) -> tuple[str | None, str | None, str | None]:
    point = Point(lon, lat)
    matches: list[tuple[str, str, str, object]] = []

    for feature in fcp_features:
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            continue
        try:
            geom = shape(geometry)
        except Exception:
            continue
        if not geom.contains(point):
            continue

        props = feature.get("properties")
        props_dict = props if isinstance(props, dict) else {}
        fcp_id = _fcp_id_from_properties(props_dict)
        label = props_dict.get("kmlDescriptionSimple")
        label_str = str(label) if label is not None else None
        code = _fcp_code_from_label(label_str)
        if fcp_id is None:
            continue
        matches.append((fcp_id, code or "", label_str or "", geom))

    if not matches:
        return None, None, None

    matches.sort(key=lambda m: m[0])
    fcp_id, code, label, _ = matches[0]
    return fcp_id, code or None, label or None


def _coordinates_from_gps(gps: dict | None) -> tuple[float, float] | None:
    if not isinstance(gps, dict):
        return None
    if gps.get("type") != "Point":
        return None
    coords = gps.get("coordinates")
    if not isinstance(coords, (list, tuple)) or len(coords) < 2:
        return None
    try:
        lon = float(coords[0])
        lat = float(coords[1])
    except (TypeError, ValueError):
        return None
    return lon, lat


def list_map_photo_markers(session: Session, project_id: str) -> list[MapPhotoMarkerRead]:
    project = session.get(Project, project_id)
    if project is None:
        raise LookupError("project not found")

    fcp_features = _load_fcp_polygon_features(session, project_id)

    statement = (
        select(ProjectAsset, PhotoAnalysis)
        .where(ProjectAsset.project_id == project_id)
        .where(ProjectAsset.kind == AssetKind.image)
        .join(PhotoAnalysis, col(PhotoAnalysis.asset_id) == col(ProjectAsset.id))
    )
    rows = session.exec(statement).all()

    markers: list[MapPhotoMarkerRead] = []
    for asset, analysis in rows:
        coords = _coordinates_from_gps(analysis.gps_coordinates)
        if coords is None:
            continue
        lon, lat = coords
        fcp_id, fcp_code, fcp_label = _assign_fcp(lon, lat, fcp_features)
        markers.append(
            MapPhotoMarkerRead(
                asset_id=asset.id,
                coordinates=(lon, lat),
                category=effective_category(analysis),
                fcp_id=fcp_id,
                fcp_code=fcp_code,
                fcp_label=fcp_label,
            )
        )

    markers.sort(key=lambda m: m.asset_id)
    return markers
