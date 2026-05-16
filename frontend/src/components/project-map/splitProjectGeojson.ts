import type { Feature, FeatureCollection } from 'geojson';

import {
  fcpCodeFromProperties,
  fcpIdFromProperties,
  fcpLabelFromProperties,
} from './fcpFromProperties';

function isPolygonFeature(feature: Feature): boolean {
  const t = feature.geometry?.type;
  return t === 'Polygon' || t === 'MultiPolygon';
}

function isLineFeature(feature: Feature): boolean {
  const t = feature.geometry?.type;
  return t === 'LineString' || t === 'MultiLineString';
}

export type SplitProjectGeojson = {
  fcpPolygons: FeatureCollection;
  trenches: FeatureCollection;
};

export function splitProjectGeojson(fc: FeatureCollection): SplitProjectGeojson {
  const fcpFeatures: Feature[] = [];
  const trenchFeatures: Feature[] = [];

  for (const feature of fc.features) {
    if (isPolygonFeature(feature)) {
      fcpFeatures.push(feature);
    } else if (isLineFeature(feature)) {
      trenchFeatures.push(feature);
    }
  }

  return {
    fcpPolygons: { type: 'FeatureCollection', features: fcpFeatures },
    trenches: { type: 'FeatureCollection', features: trenchFeatures },
  };
}

export function enrichFcpPolygons(fc: FeatureCollection): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: fc.features.map((feature) => {
      const props = (feature.properties ?? {}) as Record<string, unknown>;
      const fcpId = fcpIdFromProperties(props);
      const fcpLabel = fcpLabelFromProperties(props);
      const fcpCode = fcpCodeFromProperties(props);
      return {
        ...feature,
        properties: {
          ...props,
          fcp_id: fcpId,
          fcp_label: fcpLabel,
          fcp_code: fcpCode,
        },
      };
    }),
  };
}
