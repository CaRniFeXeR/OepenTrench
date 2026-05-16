import { useMemo } from 'react';
import type { Feature, FeatureCollection } from 'geojson';

import { fcpCodeFromProperties, fcpLabelFromProperties } from '../fcpFromProperties';
import { enrichFcpPolygons, splitProjectGeojson } from '../splitProjectGeojson';

export function useMapGeoLayers(mapData: FeatureCollection, selectedFcpId: string | null) {
  const { fcpPolygons, trenches } = useMemo(() => {
    const split = splitProjectGeojson(mapData);
    return {
      fcpPolygons: enrichFcpPolygons(split.fcpPolygons),
      trenches: split.trenches,
    };
  }, [mapData]);

  const selectedFcpFeature = useMemo((): Feature | null => {
    if (!selectedFcpId) return null;
    return (
      fcpPolygons.features.find((f) => {
        const props = (f.properties ?? {}) as Record<string, unknown>;
        return String(props.fcp_id ?? '') === selectedFcpId;
      }) ?? null
    );
  }, [fcpPolygons, selectedFcpId]);

  const fcpLabel = selectedFcpFeature
    ? fcpLabelFromProperties(
        (selectedFcpFeature.properties ?? {}) as Record<string, unknown>,
      )
    : '';
  const fcpCode = selectedFcpFeature
    ? fcpCodeFromProperties(
        (selectedFcpFeature.properties ?? {}) as Record<string, unknown>,
      )
    : '';

  const fitToFcpFeature = (fcpId: string): Feature | undefined => {
    return fcpPolygons.features.find((f) => {
      const props = (f.properties ?? {}) as Record<string, unknown>;
      return String(props.fcp_id ?? '') === fcpId;
    });
  };

  return {
    fcpPolygons,
    trenches,
    fcpLabel,
    fcpCode,
    fitToFcpFeature,
  };
}
