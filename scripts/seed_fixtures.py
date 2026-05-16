"""Fixture data for scripts/seed_dummy_project.py."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from shapely.geometry import shape
from shapely.ops import unary_union

from src.api.helpers.photo_documentation_category import automated_category
from src.api.helpers.time import utc_now
from src.api.models import PhotoAnalysis, PhotoDocumentationCategory

GEOJSON_BASE = "CLP20417A-P1-B00"


def _load_geojson(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _feature_geometries(doc: dict) -> list:
    doc_type = doc.get("type")
    if doc_type == "FeatureCollection":
        features = doc.get("features") or []
    elif doc_type == "Feature":
        features = [doc]
    else:
        return []
    geoms = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry")
        if geometry:
            geoms.append(shape(geometry))
    return geoms


def _point_geojson(lon: float, lat: float) -> dict[str, Any]:
    return {"type": "Point", "coordinates": [lon, lat]}


def _representative_points(doc: dict, count: int) -> list[dict[str, Any]]:
    geoms = _feature_geometries(doc)
    if not geoms:
        return []
    points: list[dict[str, Any]] = []
    for geom in geoms[:count]:
        pt = geom.representative_point()
        points.append(_point_geojson(pt.x, pt.y))
    return points


def _trench_midpoints(doc: dict, count: int) -> list[dict[str, Any]]:
    geoms = _feature_geometries(doc)
    if not geoms:
        return []
    step = max(1, len(geoms) // count)
    points: list[dict[str, Any]] = []
    for i in range(count):
        idx = min(i * step, len(geoms) - 1)
        geom = geoms[idx]
        if geom.geom_type == "LineString":
            pt = geom.interpolate(0.5, normalized=True)
        else:
            pt = geom.representative_point()
        points.append(_point_geojson(pt.x, pt.y))
    return points


def _off_site_points(doc: dict, count: int) -> list[dict[str, Any]]:
    geoms = _feature_geometries(doc)
    if not geoms:
        return []
    combined = unary_union(geoms)
    minx, miny, maxx, maxy = combined.bounds
    width = maxx - minx
    height = maxy - miny
    offsets = [
        (minx - 0.15 * width, (miny + maxy) / 2),
        ((minx + maxx) / 2, maxy + 0.12 * height),
        (maxx + 0.18 * width, miny - 0.08 * height),
    ]
    return [_point_geojson(lon, lat) for lon, lat in offsets[:count]]


def build_seed_locations(geojson_dir: Path) -> list[dict[str, Any]]:
    """Return 20 GPS points: 9 FCP, 8 trench, 3 off-site."""
    fcp_polys = _load_geojson(geojson_dir / f"{GEOJSON_BASE}_FCP_Polygons.geojson")
    trenches = _load_geojson(geojson_dir / f"{GEOJSON_BASE}_Trenches.geojson")
    cluster = _load_geojson(geojson_dir / f"{GEOJSON_BASE}_SiteCluster_Polygons.geojson")

    fcp_pts = _representative_points(fcp_polys, 9)
    trench_pts = _trench_midpoints(trenches, 8)
    off_pts = _off_site_points(cluster, 3)

    locations = fcp_pts + trench_pts + off_pts
    if len(locations) < 20:
        raise ValueError(f"expected 20 GPS locations, got {len(locations)}")
    return locations[:20]


@dataclass(frozen=True)
class SeedScenario:
    """Analysis field overrides for one seeded photo."""

    location_index: int
    is_in_domain: bool = True
    has_white_paper: bool = True
    has_ruler: bool = True
    estimated_depth: float | None = 1.2
    has_duct: bool = True
    estimate_number_of_ducts: int | None = 1
    has_gdpr_problems: bool = False
    is_duplicated: bool = False
    gps_matches_route: bool = True
    date_valid: bool = True
    is_false_call: bool = False
    reviewer_has_duct: bool | None = None
    reviewer_has_ruler: bool | None = None
    reviewer_is_in_domain: bool | None = None
    reviewer_has_gdpr_problems: bool | None = None
    reviewer_gps_matches_route: bool | None = None
    reviewer_override_category: PhotoDocumentationCategory | None = None
    reviewed_at: datetime | None = None

    def to_analysis_fields(self, gps_coordinates: dict[str, Any]) -> dict[str, Any]:
        return {
            "is_in_domain": self.is_in_domain,
            "has_white_paper": self.has_white_paper,
            "has_ruler": self.has_ruler,
            "estimated_depth": self.estimated_depth,
            "has_duct": self.has_duct,
            "estimate_number_of_ducts": self.estimate_number_of_ducts,
            "has_gdpr_problems": self.has_gdpr_problems,
            "is_duplicated": self.is_duplicated,
            "gps_matches_route": self.gps_matches_route,
            "date_valid": self.date_valid,
            "is_false_call": self.is_false_call,
            "gps_coordinates": gps_coordinates,
            "reviewer_has_duct": self.reviewer_has_duct,
            "reviewer_has_ruler": self.reviewer_has_ruler,
            "reviewer_is_in_domain": self.reviewer_is_in_domain,
            "reviewer_has_gdpr_problems": self.reviewer_has_gdpr_problems,
            "reviewer_gps_matches_route": self.reviewer_gps_matches_route,
            "reviewer_override_category": self.reviewer_override_category,
            "reviewed_at": self.reviewed_at,
        }


def _reviewed() -> datetime:
    return utc_now()


# 7 green, 5 red, 8 yellow — locations chosen so red off-route cases use indices 17–19.
SEED_SCENARIOS: tuple[SeedScenario, ...] = (
    # --- green (7) ---
    SeedScenario(0),
    SeedScenario(1, reviewed_at=_reviewed()),
    SeedScenario(2, reviewed_at=_reviewed()),
    SeedScenario(3, reviewed_at=_reviewed()),
    SeedScenario(4),
    SeedScenario(5, reviewed_at=_reviewed()),
    SeedScenario(6),
    # --- red (5) ---
    SeedScenario(7, is_in_domain=False),
    SeedScenario(17, gps_matches_route=False),
    SeedScenario(18, is_in_domain=False, gps_matches_route=False),
    SeedScenario(8, is_in_domain=False),
    SeedScenario(19, gps_matches_route=False),
    # --- yellow (8) ---
    SeedScenario(9, has_ruler=False),
    SeedScenario(10, has_duct=False, estimate_number_of_ducts=0),
    SeedScenario(11, has_gdpr_problems=True),
    SeedScenario(12, has_white_paper=False, has_ruler=False),
    SeedScenario(
        13,
        has_ruler=False,
        reviewer_has_ruler=True,
        reviewed_at=_reviewed(),
    ),
    SeedScenario(
        14,
        has_ruler=False,
        has_duct=False,
        reviewer_override_category=PhotoDocumentationCategory.green,
        reviewed_at=_reviewed(),
    ),
    SeedScenario(
        15,
        has_gdpr_problems=True,
        reviewer_has_gdpr_problems=False,
        reviewed_at=_reviewed(),
    ),
    SeedScenario(
        16,
        is_duplicated=True,
        has_ruler=False,
        has_duct=False,
    ),
)


def apply_scenario_to_row(
    row: PhotoAnalysis,
    scenario: SeedScenario,
    gps_coordinates: dict[str, Any],
) -> None:
    fields = scenario.to_analysis_fields(gps_coordinates)
    for key, value in fields.items():
        setattr(row, key, value)
    row.updated_at = utc_now()
    row.category = automated_category(row)


def expected_category_counts() -> dict[str, int]:
    counts: dict[str, int] = {"green": 0, "yellow": 0, "red": 0}
    for scenario in SEED_SCENARIOS:
        dummy = PhotoAnalysis(
            asset_id="preview",
            **{k: v for k, v in scenario.to_analysis_fields({"type": "Point", "coordinates": [0, 0]}).items() if k != "gps_coordinates"},
        )
        cat = automated_category(dummy)
        counts[cat.value] += 1
    return counts
