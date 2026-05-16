import type { Feature, FeatureCollection, LineString } from 'geojson';

import type { FcpCoverageCompartmentRead } from '../../api/client';

export function buildCoverageCompartmentCollection(
  compartments: FcpCoverageCompartmentRead[],
): FeatureCollection {
  const features: Feature<LineString>[] = compartments.map((comp) => ({
    type: 'Feature',
    id: comp.id,
    properties: {
      covered: comp.covered,
      fcp_id: comp.fcp_id,
      length_m: comp.length_m,
    },
    geometry: comp.geometry as unknown as LineString,
  }));

  return { type: 'FeatureCollection', features };
}
