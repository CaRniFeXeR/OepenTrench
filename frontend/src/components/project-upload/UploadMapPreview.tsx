import { useId, useRef } from 'react';
import type { MapRef } from 'react-map-gl/maplibre';
import type { FeatureCollection } from 'geojson';

import { MapView } from '../map/MapView';
import { GeoJsonRouteLayers } from '../map/GeoJsonRouteLayers';
import { useMapFitToFeatureCollection } from '../map/useMapFitToFeatureCollection';

export function UploadMapPreview({
  featureCollection,
  height = 420,
}: {
  featureCollection: FeatureCollection | null;
  height?: number;
}) {
  const mapRef = useRef<MapRef | null>(null);
  const reactId = useId();
  const sourceId = `upload-preview-${reactId.replace(/:/g, '')}`;

  const { initialBounds, fitBoundsOptions, onMapLoad } =
    useMapFitToFeatureCollection(mapRef, featureCollection);

  return (
    <div className="flex h-full min-h-[280px] flex-col rounded-xl border border-slate-200 bg-white shadow-sm">
      {featureCollection ? (
        <MapView
          ref={mapRef}
          className="overflow-hidden rounded-xl"
          height={height}
          bounds={initialBounds}
          fitBoundsOptions={fitBoundsOptions}
          onLoad={onMapLoad}
        >
          <GeoJsonRouteLayers data={featureCollection} sourceId={sourceId} />
        </MapView>
      ) : (
        <div
          className="flex flex-1 flex-col items-center justify-center rounded-xl bg-slate-100 px-6 text-center text-slate-500"
          style={{ minHeight: height }}
        >
          <p className="max-w-sm text-sm font-medium">
            Your map will appear here as files are uploaded.
          </p>
          <p className="mt-2 max-w-sm text-xs">
            Upload a GeoJSON route file to see the route on the map. Photo-only
            uploads are not drawn here until an analyse pipeline provides
            coordinates.
          </p>
        </div>
      )}
    </div>
  );
}
