import { useCallback, useEffect, useState } from 'react';
import type { FeatureCollection } from 'geojson';

import { readProjectGeojsonProjectsProjectIdGeojsonGet } from '../../api/client';
import {
  normalizeFeatureCollection,
  stripBlankFillColors,
} from '../../normalizeExampleGeojson';

function mergeFeatureCollections(
  existing: FeatureCollection | null,
  added: FeatureCollection,
): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: [...(existing?.features ?? []), ...added.features],
  };
}

export function useProjectMapGeojson(
  projectId: string,
  geojsonStatus: 'missing' | 'ready',
) {
  const [mapData, setMapData] = useState<FeatureCollection | null>(null);

  useEffect(() => {
    if (geojsonStatus !== 'ready') return;

    let cancelled = false;
    void (async () => {
      const { data, error } = await readProjectGeojsonProjectsProjectIdGeojsonGet({
        path: { project_id: projectId },
      });
      if (cancelled || error || !data) return;
      const fc = stripBlankFillColors(
        normalizeFeatureCollection(data as unknown),
      );
      setMapData(fc);
    })();

    return () => {
      cancelled = true;
    };
  }, [projectId, geojsonStatus]);

  const mergeMapData = useCallback((added: FeatureCollection) => {
    setMapData((prev) => mergeFeatureCollections(prev, added));
  }, []);

  return { mapData, mergeMapData };
}
