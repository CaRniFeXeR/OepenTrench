import { useCallback, useEffect, useMemo, type RefObject } from 'react';
import type { MapRef } from 'react-map-gl/maplibre';
import type { FeatureCollection } from 'geojson';
import type {
  LngLatBoundsLike,
  Map as MaplibreMap,
  MapLibreEvent,
} from 'maplibre-gl';

import {
  boundsToLngLatBoundsLike,
  featureCollectionBounds,
  fitMapToFeatureCollection,
  MAP_FIT_DEFAULT_OPTIONS,
} from './geoBounds';

function scheduleFit(
  map: MaplibreMap,
  featureCollection: FeatureCollection,
): void {
  const runFit = () => fitMapToFeatureCollection(map, featureCollection);

  if (map.isStyleLoaded()) {
    runFit();
    return;
  }

  map.once('load', runFit);
}

export function useMapFitToFeatureCollection(
  mapRef: RefObject<MapRef | null>,
  featureCollection: FeatureCollection | null,
) {
  const initialBounds = useMemo((): LngLatBoundsLike | undefined => {
    if (!featureCollection) return undefined;
    const box = featureCollectionBounds(featureCollection);
    if (!box) return undefined;
    return boundsToLngLatBoundsLike(box);
  }, [featureCollection]);

  const onMapLoad = useCallback(
    (_e: MapLibreEvent) => {
      const map = mapRef.current?.getMap();
      if (!map || !featureCollection) return;
      scheduleFit(map, featureCollection);
    },
    [mapRef, featureCollection],
  );

  useEffect(() => {
    const map = mapRef.current?.getMap();
    if (!map || !featureCollection) return;

    const runFit = () => fitMapToFeatureCollection(map, featureCollection);

    if (map.isStyleLoaded()) {
      runFit();
      return;
    }

    map.once('load', runFit);
    return () => {
      map.off('load', runFit);
    };
  }, [mapRef, featureCollection]);

  return {
    initialBounds,
    fitBoundsOptions: MAP_FIT_DEFAULT_OPTIONS,
    onMapLoad,
  };
}
