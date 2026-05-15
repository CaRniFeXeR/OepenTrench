import type { Feature, FeatureCollection } from 'geojson';

function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * Roots like SiteCluster polygons may omit RFC 7946 `type`. Non-compliant `crs`
 * is dropped when rebuilding a normalized collection.
 */
export function normalizeFeatureCollection(parsed: unknown): FeatureCollection {
  if (!isPlainRecord(parsed) || !Array.isArray(parsed.features)) {
    return { type: 'FeatureCollection', features: [] };
  }
  return {
    type: 'FeatureCollection',
    features: parsed.features as FeatureCollection['features'],
  };
}

export function stripBlankFillColors(fc: FeatureCollection): FeatureCollection {
  return {
    ...fc,
    features: fc.features.map((feat) => {
      const props = feat.properties;
      if (!isPlainRecord(props) || !('fillColor' in props)) return feat;
      const raw = props.fillColor;
      if (raw != null && String(raw).trim() !== '') return feat;

      const nextProps = { ...props };
      delete nextProps.fillColor;

      return {
        ...feat,
        properties: Object.keys(nextProps).length > 0 ? nextProps : null,
      } as Feature;
    }),
  };
}
