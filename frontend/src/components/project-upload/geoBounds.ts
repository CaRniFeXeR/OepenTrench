import type { FeatureCollection } from 'geojson';

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
