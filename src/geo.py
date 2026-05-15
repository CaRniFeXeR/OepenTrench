"""GeoJSON loading + simple spatial helpers for the trench dataset.

The dataset includes one project (CLP20417A-P1-B00) with:
- Trenches (~2,983 LineStrings) — actual underground duct routes
- FCPs (Fiber Connection Points, 9 buildings)
- FCP_Polygons, SiteCluster_Polygons
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import geopandas as gpd
from shapely.geometry import LineString, Point, shape


@dataclass
class ProjectGeo:
    trenches: gpd.GeoDataFrame
    fcps: gpd.GeoDataFrame
    fcp_polys: gpd.GeoDataFrame
    cluster: gpd.GeoDataFrame
    crs_metric: str = "EPSG:31287"  # Austrian MGI / Lambert, good for length & buffer in metres


def _load(p: Path) -> gpd.GeoDataFrame:
    if not p.exists():
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    gdf = gpd.read_file(p)
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    return gdf


def load_project(geojson_dir: Path) -> ProjectGeo:
    base = "CLP20417A-P1-B00"
    return ProjectGeo(
        trenches=_load(geojson_dir / f"{base}_Trenches.geojson"),
        fcps=_load(geojson_dir / f"{base}_FCPs.geojson"),
        fcp_polys=_load(geojson_dir / f"{base}_FCP_Polygons.geojson"),
        cluster=_load(geojson_dir / f"{base}_SiteCluster_Polygons.geojson"),
    )


def to_metric(gdf: gpd.GeoDataFrame, target: str = "EPSG:31287") -> gpd.GeoDataFrame:
    return gdf.to_crs(target)


def bbox_center(gdf: gpd.GeoDataFrame) -> Tuple[float, float]:
    minx, miny, maxx, maxy = gdf.total_bounds
    return (miny + maxy) / 2, (minx + maxx) / 2  # (lat, lon) for folium
