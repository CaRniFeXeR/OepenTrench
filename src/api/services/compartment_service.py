from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from pyproj import Transformer
from shapely.geometry import LineString, MultiLineString, Point, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import substring, transform
from shapely.strtree import STRtree
from sqlmodel import Session, col, select

from src.api.helpers.time import utc_now
from src.api.models import (
    AssetKind,
    FcpCoverageCompartment,
    FcpCoverageCompartmentRead,
    FcpCoverageRead,
    FcpCoverageSummary,
    FcpCoverageSummaryRead,
    GeojsonStatus,
    PhotoAnalysis,
    Project,
    ProjectAsset,
    ProjectCoverageSummaryRead,
    ProjectFcpCoverage,
)
from src.api.services.project_asset_service import (
    FCP_POLYGONS_SUFFIX,
    TRENCHES_SUFFIX,
    _geojson_asset_for_suffix,
    geojson_assets_for_project,
    validate_geojson_bytes,
)
from src.api.uploads import ensure_upload_root_exists, project_asset_abs_path

COMPARTMENT_LENGTH_M = 5.0
PHOTO_CAPTURE_RADIUS_M = 7.0
METRIC_CRS = "EPSG:31287"
WGS84_CRS = "EPSG:4326"

_FCP_CODE_RE = re.compile(r"^(\S+)")

_transform_to_metric = Transformer.from_crs(WGS84_CRS, METRIC_CRS, always_xy=True)
_transform_to_wgs84 = Transformer.from_crs(METRIC_CRS, WGS84_CRS, always_xy=True)


@dataclass
class _Compartment:
    id: str
    fcp_id: str
    length_m: float
    center_metric: Point
    line_metric: LineString
    covered: bool = False


@dataclass
class _FcpContext:
    fcp_id: str
    fcp_code: str | None
    fcp_label: str | None
    polygon_metric: BaseGeometry


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


def _is_connected_to_home(props: dict | None) -> bool:
    if not props:
        return False
    val = props.get("isConnectedToHome")
    if val is True or val == 1:
        return True
    if isinstance(val, str) and val.strip().lower() in ("true", "1", "yes"):
        return True
    return False


def _to_metric(geom: BaseGeometry) -> BaseGeometry:
    return transform(_transform_to_metric.transform, geom)


def _to_wgs84(geom: BaseGeometry) -> BaseGeometry:
    return transform(_transform_to_wgs84.transform, geom)


def _load_geojson_features(session: Session, project_id: str, suffix: str) -> list[dict]:
    assets = geojson_assets_for_project(session, project_id)
    asset = _geojson_asset_for_suffix(assets, suffix)
    if asset is None:
        return []

    upload_root = ensure_upload_root_exists()
    abs_path = project_asset_abs_path(
        upload_root=upload_root,
        stored_relpath=asset.stored_relpath,
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


def _line_parts(geom: BaseGeometry) -> list[LineString]:
    if geom.is_empty:
        return []
    if isinstance(geom, LineString):
        return [geom]
    if isinstance(geom, MultiLineString):
        return [g for g in geom.geoms if not g.is_empty]
    if geom.geom_type == "GeometryCollection":
        parts: list[LineString] = []
        for g in geom.geoms:
            parts.extend(_line_parts(g))
        return parts
    return []


def _split_line_into_compartments(
    line_metric: LineString,
    *,
    fcp_id: str,
    trench_index: int,
    line_index: int,
) -> list[_Compartment]:
    length = line_metric.length
    if length <= 0:
        return []

    compartments: list[_Compartment] = []
    offset = 0.0
    seq = 0
    while offset < length:
        end = min(offset + COMPARTMENT_LENGTH_M, length)
        comp_geom = substring(line_metric, offset, end)
        if not isinstance(comp_geom, LineString) or comp_geom.is_empty:
            break
        center = comp_geom.interpolate(0.5, normalized=True)
        comp_id = f"{fcp_id}:t{trench_index}:l{line_index}:c{seq}"
        compartments.append(
            _Compartment(
                id=comp_id,
                fcp_id=fcp_id,
                length_m=end - offset,
                center_metric=center,
                line_metric=comp_geom,
            )
        )
        offset = end
        seq += 1
    return compartments


def _load_fcp_contexts(features: list[dict]) -> list[_FcpContext]:
    contexts: list[_FcpContext] = []
    for feature in features:
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            continue
        try:
            geom = shape(geometry)
        except Exception:
            continue
        if geom.is_empty:
            continue

        props = feature.get("properties")
        props_dict = props if isinstance(props, dict) else {}
        fcp_id = _fcp_id_from_properties(props_dict)
        if fcp_id is None:
            continue
        label = props_dict.get("kmlDescriptionSimple")
        label_str = str(label) if label is not None else None
        contexts.append(
            _FcpContext(
                fcp_id=fcp_id,
                fcp_code=_fcp_code_from_label(label_str),
                fcp_label=label_str,
                polygon_metric=_to_metric(geom),
            )
        )
    return contexts


def _build_compartments_for_fcp(
    fcp: _FcpContext,
    trench_features: list[dict],
    *,
    trench_index_offset: int = 0,
) -> list[_Compartment]:
    compartments: list[_Compartment] = []
    trench_index = trench_index_offset

    for feature in trench_features:
        props = feature.get("properties")
        props_dict = props if isinstance(props, dict) else {}
        if _is_connected_to_home(props_dict):
            continue

        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            continue
        try:
            geom_wgs84 = shape(geometry)
        except Exception:
            continue
        if geom_wgs84.is_empty:
            continue

        geom_metric = _to_metric(geom_wgs84)
        if not geom_metric.intersects(fcp.polygon_metric):
            continue

        clipped = geom_metric.intersection(fcp.polygon_metric)
        for line_index, line_part in enumerate(_line_parts(clipped)):
            compartments.extend(
                _split_line_into_compartments(
                    line_part,
                    fcp_id=fcp.fcp_id,
                    trench_index=trench_index,
                    line_index=line_index,
                )
            )
        trench_index += 1

    return compartments


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


def _load_photo_points_metric(session: Session, project_id: str) -> list[Point]:
    statement = (
        select(PhotoAnalysis)
        .join(ProjectAsset, col(PhotoAnalysis.asset_id) == col(ProjectAsset.id))
        .where(ProjectAsset.project_id == project_id)
        .where(ProjectAsset.kind == AssetKind.image)
    )
    rows = session.exec(statement).all()
    points: list[Point] = []
    for analysis in rows:
        coords = _coordinates_from_gps(analysis.gps_coordinates)
        if coords is None:
            continue
        lon, lat = coords
        points.append(_to_metric(Point(lon, lat)))
    return points


def _mark_covered(compartments: list[_Compartment], photo_points_metric: list[Point]) -> None:
    if not compartments or not photo_points_metric:
        return

    tree = STRtree(photo_points_metric)
    radius = PHOTO_CAPTURE_RADIUS_M
    for comp in compartments:
        candidates = tree.query(comp.center_metric.buffer(radius))
        for idx in candidates:
            if comp.center_metric.distance(photo_points_metric[int(idx)]) <= radius:
                comp.covered = True
                break


def _build_compartments(
    session: Session,
    project_id: str,
    *,
    fcp_id_filter: str | None = None,
) -> list[_Compartment]:
    fcp_features = _load_geojson_features(session, project_id, FCP_POLYGONS_SUFFIX)
    trench_features = _load_geojson_features(session, project_id, TRENCHES_SUFFIX)
    fcp_contexts = _load_fcp_contexts(fcp_features)

    if fcp_id_filter is not None:
        fcp_contexts = [f for f in fcp_contexts if f.fcp_id == fcp_id_filter]

    all_compartments: list[_Compartment] = []
    for fcp in fcp_contexts:
        all_compartments.extend(_build_compartments_for_fcp(fcp, trench_features))

    photo_points = _load_photo_points_metric(session, project_id)
    _mark_covered(all_compartments, photo_points)
    return all_compartments


def _compartment_to_read(comp: _Compartment) -> FcpCoverageCompartmentRead:
    line_wgs84 = _to_wgs84(comp.line_metric)
    center_wgs84 = _to_wgs84(comp.center_metric)
    if not isinstance(center_wgs84, Point):
        raise ValueError("compartment center must be a point")
    return FcpCoverageCompartmentRead(
        id=comp.id,
        fcp_id=comp.fcp_id,
        covered=comp.covered,
        length_m=comp.length_m,
        center=(float(center_wgs84.x), float(center_wgs84.y)),
        geometry=mapping(line_wgs84),
    )


def _summaries_from_compartments(
    compartments: list[_Compartment],
    fcp_contexts: list[_FcpContext],
) -> list[FcpCoverageSummaryRead]:
    by_fcp: dict[str, list[_Compartment]] = {}
    for comp in compartments:
        by_fcp.setdefault(comp.fcp_id, []).append(comp)

    context_by_id = {c.fcp_id: c for c in fcp_contexts}
    summaries: list[FcpCoverageSummaryRead] = []
    for fcp_id, comps in sorted(by_fcp.items()):
        ctx = context_by_id.get(fcp_id)
        covered_count = sum(1 for c in comps if c.covered)
        total = len(comps)
        summaries.append(
            FcpCoverageSummaryRead(
                fcp_id=fcp_id,
                fcp_code=ctx.fcp_code if ctx else None,
                fcp_label=ctx.fcp_label if ctx else None,
                compartment_count=total,
                covered_count=covered_count,
                coverage_ratio=covered_count / total if total else 0.0,
            )
        )
    return summaries


def photo_matches_route(
    session: Session,
    project_id: str,
    lon: float,
    lat: float,
) -> bool:
    compartments = _build_compartments(session, project_id)
    if not compartments:
        return False
    point = _to_metric(Point(lon, lat))
    radius = PHOTO_CAPTURE_RADIUS_M
    for comp in compartments:
        if point.distance(comp.center_metric) <= radius:
            return True
    return False


def aggregate_project_summary(
    summaries: list[FcpCoverageSummaryRead],
    *,
    computed_at: datetime | None,
) -> ProjectCoverageSummaryRead:
    compartment_count = sum(s.compartment_count for s in summaries)
    covered_count = sum(s.covered_count for s in summaries)
    return ProjectCoverageSummaryRead(
        compartment_count=compartment_count,
        covered_count=covered_count,
        coverage_ratio=covered_count / compartment_count if compartment_count else 0.0,
        fcp_count=len(summaries),
        computed_at=computed_at,
    )


def _empty_fcp_coverage_read() -> FcpCoverageRead:
    return FcpCoverageRead(
        project=aggregate_project_summary([], computed_at=None),
        compartments=[],
        summaries=[],
    )


def save_fcp_coverage(session: Session, project_id: str, result: FcpCoverageRead) -> None:
    computed_at = result.project.computed_at or utc_now()

    for row in session.exec(
        select(FcpCoverageCompartment).where(
            FcpCoverageCompartment.project_id == project_id,
        )
    ).all():
        session.delete(row)
    for row in session.exec(
        select(FcpCoverageSummary).where(FcpCoverageSummary.project_id == project_id)
    ).all():
        session.delete(row)

    meta = session.get(ProjectFcpCoverage, project_id)
    if meta is None:
        session.add(ProjectFcpCoverage(project_id=project_id, computed_at=computed_at))
    else:
        meta.computed_at = computed_at
        session.add(meta)

    for summary in result.summaries:
        session.add(
            FcpCoverageSummary(
                project_id=project_id,
                fcp_id=summary.fcp_id,
                fcp_code=summary.fcp_code,
                fcp_label=summary.fcp_label,
                compartment_count=summary.compartment_count,
                covered_count=summary.covered_count,
                coverage_ratio=summary.coverage_ratio,
            )
        )

    for comp in result.compartments:
        session.add(
            FcpCoverageCompartment(
                id=comp.id,
                project_id=project_id,
                fcp_id=comp.fcp_id,
                covered=comp.covered,
                length_m=comp.length_m,
                center={"coordinates": [comp.center[0], comp.center[1]]},
                geometry=comp.geometry,
            )
        )

    session.commit()


def load_fcp_coverage(session: Session, project_id: str) -> FcpCoverageRead:
    _require_project_geojson_ready(session, project_id)

    meta = session.get(ProjectFcpCoverage, project_id)
    if meta is None:
        return _empty_fcp_coverage_read()

    summary_rows = session.exec(
        select(FcpCoverageSummary)
        .where(FcpCoverageSummary.project_id == project_id)
        .order_by(FcpCoverageSummary.fcp_id)
    ).all()
    summaries = [
        FcpCoverageSummaryRead(
            fcp_id=row.fcp_id,
            fcp_code=row.fcp_code,
            fcp_label=row.fcp_label,
            compartment_count=row.compartment_count,
            covered_count=row.covered_count,
            coverage_ratio=row.coverage_ratio,
        )
        for row in summary_rows
    ]

    compartment_rows = session.exec(
        select(FcpCoverageCompartment).where(
            FcpCoverageCompartment.project_id == project_id,
        )
    ).all()
    compartments = [_compartment_row_to_read(row) for row in compartment_rows]

    return FcpCoverageRead(
        project=aggregate_project_summary(summaries, computed_at=meta.computed_at),
        compartments=compartments,
        summaries=summaries,
    )


def _compartment_row_to_read(row: FcpCoverageCompartment) -> FcpCoverageCompartmentRead:
    center_data = row.center if isinstance(row.center, dict) else {}
    coords = center_data.get("coordinates")
    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
        center = (float(coords[0]), float(coords[1]))
    else:
        center = (0.0, 0.0)
    geometry = row.geometry if isinstance(row.geometry, dict) else {}
    return FcpCoverageCompartmentRead(
        id=row.id,
        fcp_id=row.fcp_id,
        covered=row.covered,
        length_m=row.length_m,
        center=center,
        geometry=geometry,
    )


def _require_project_geojson_ready(session: Session, project_id: str) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise LookupError("project not found")
    if project.geojson_status != GeojsonStatus.ready:
        raise ValueError("required GeoJSON files are not ready")
    return project


def compute_fcp_coverage(session: Session, project_id: str) -> FcpCoverageRead:
    _require_project_geojson_ready(session, project_id)

    fcp_features = _load_geojson_features(session, project_id, FCP_POLYGONS_SUFFIX)
    fcp_contexts = _load_fcp_contexts(fcp_features)

    compartments = _build_compartments(session, project_id)
    summaries = _summaries_from_compartments(compartments, fcp_contexts)
    computed_at = utc_now()

    return FcpCoverageRead(
        project=aggregate_project_summary(summaries, computed_at=computed_at),
        compartments=[_compartment_to_read(c) for c in compartments],
        summaries=summaries,
    )


def calculate_and_save_fcp_coverage(session: Session, project_id: str) -> FcpCoverageRead:
    result = compute_fcp_coverage(session, project_id)
    save_fcp_coverage(session, project_id, result)
    return result
