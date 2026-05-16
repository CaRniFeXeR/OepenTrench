import type { FeatureCollection } from 'geojson';
import type { LngLatBoundsLike, Map as MaplibreMap } from 'maplibre-gl';

export const MAP_FIT_PADDING = 48;
export const MAP_FIT_MAX_ZOOM = 15;

export const MAP_FIT_DEFAULT_OPTIONS = {
  padding: MAP_FIT_PADDING,
  maxZoom: MAP_FIT_MAX_ZOOM,
} as const;

function expandBounds(
  bounds: [number, number, number, number],
  lon: number,
  lat: number,
): [number, number, number, number] {
  const [w, s, e, n] = bounds;
  return [
    Math.min(w, lon),
    Math.min(s, lat),
    Math.max(e, lon),
    Math.max(n, lat),
  ];
}

function walkCoordinates(
  bounds: [number, number, number, number],
  coords: unknown,
): [number, number, number, number] {
  if (
    Array.isArray(coords) &&
    coords.length >= 2 &&
    typeof coords[0] === 'number' &&
    typeof coords[1] === 'number'
  ) {
    return expandBounds(bounds, coords[0], coords[1]);
  }

  if (!Array.isArray(coords)) return bounds;

  let b = bounds;
  for (const part of coords) {
    b = walkCoordinates(b, part);
  }
  return b;
}

function geometryBounds(
  bounds: [number, number, number, number],
  geom: { type: string; coordinates?: unknown },
): [number, number, number, number] {
  if (!geom.coordinates) return bounds;
  return walkCoordinates(bounds, geom.coordinates);
}

/**
 * Returns [west, south, east, north] in WGS84, or null if empty.
 */
export function featureCollectionBounds(
  fc: FeatureCollection,
): [number, number, number, number] | null {
  let b: [number, number, number, number] = [
    Infinity,
    Infinity,
    -Infinity,
    -Infinity,
  ];

  for (const f of fc.features) {
    const g = f.geometry;
    if (!g || typeof g !== 'object' || !('type' in g)) continue;
    b = geometryBounds(b, g as { type: string; coordinates?: unknown });
  }

  if (
    !Number.isFinite(b[0]) ||
    !Number.isFinite(b[1]) ||
    !Number.isFinite(b[2]) ||
    !Number.isFinite(b[3])
  ) {
    return null;
  }

  return b;
}

export function boundsToLngLatBoundsLike(
  box: [number, number, number, number],
): LngLatBoundsLike {
  const [w, s, e, n] = box;
  return [
    [w, s],
    [e, n],
  ];
}

export function fitMapToFeatureCollection(
  map: MaplibreMap,
  fc: FeatureCollection,
  options?: { duration?: number },
): void {
  const box = featureCollectionBounds(fc);
  if (!box) return;

  const [w, s, e, n] = box;
  const duration = options?.duration ?? 600;

  if (w === e && s === n) {
    map.easeTo({
      center: [w, s],
      zoom: 14,
      duration: Math.min(duration, 500),
    });
    return;
  }

  map.fitBounds(boundsToLngLatBoundsLike(box), {
    ...MAP_FIT_DEFAULT_OPTIONS,
    duration,
  });
}
