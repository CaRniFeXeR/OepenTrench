from __future__ import annotations

import logging
import random

from shapely.geometry import shape
from shapely.ops import unary_union


def random_point_in_geojson_bounds(geojson: dict) -> dict:
    """Return a GeoJSON Point with coordinates uniformly sampled in the union bbox."""
    features = geojson.get("features")
    if not features:
        raise ValueError("GeoJSON has no features")

    geoms = []
    for feature in features:
        geometry = feature.get("geometry") if isinstance(feature, dict) else None
        if geometry:
            geoms.append(shape(geometry))

    if not geoms:
        raise ValueError("GeoJSON has no geometries")

    combined = unary_union(geoms)
    minx, miny, maxx, maxy = combined.bounds
    lon = random.uniform(minx, maxx)
    lat = random.uniform(miny, maxy)
    logging.info(f"Random point in geojson bounds: {lon}, {lat}")
    return {"type": "Point", "coordinates": [lon, lat]}
