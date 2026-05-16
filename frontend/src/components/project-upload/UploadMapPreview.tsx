import { Layer, Source } from 'react-map-gl/maplibre';
import { useCallback, useEffect, useMemo, useRef, useId } from 'react';
import type { MapRef } from 'react-map-gl/maplibre';
import type { FeatureCollection } from 'geojson';
import type {
  CircleLayerSpecification,
  FillLayerSpecification,
  FilterSpecification,
  LineLayerSpecification,
} from '@maplibre/maplibre-gl-style-spec';

import { MapView } from '../MapView';
import {
  boundsToLngLatBoundsLike,
  featureCollectionBounds,
  fitMapToFeatureCollection,
  MAP_FIT_MAX_ZOOM,
  MAP_FIT_PADDING,
} from './geoBounds';

const ROUTE_BLUE = '#3b82f6';

const FILTER_POLYGON: FilterSpecification = [
  'any',
  ['==', ['geometry-type'], 'Polygon'],
  ['==', ['geometry-type'], 'MultiPolygon'],
];

const FILTER_LINE: FilterSpecification = [
  'any',
  ['==', ['geometry-type'], 'LineString'],
  ['==', ['geometry-type'], 'MultiLineString'],
];

const FILTER_POINT: FilterSpecification = [
  '==',
  ['geometry-type'],
  'Point',
];

const fillPaint = {
  'fill-color': ROUTE_BLUE,
  'fill-opacity': 0.25,
} as NonNullable<FillLayerSpecification['paint']>;

const polygonOutlinePaint = {
  'line-color': ROUTE_BLUE,
  'line-width': 2,
} as NonNullable<LineLayerSpecification['paint']>;

const linePaint = {
  'line-color': ROUTE_BLUE,
  'line-width': 3,
} as NonNullable<LineLayerSpecification['paint']>;

const circlePaint = {
  'circle-radius': 5,
  'circle-color': ROUTE_BLUE,
  'circle-stroke-width': 1,
  'circle-stroke-color': '#1e293b',
} as NonNullable<CircleLayerSpecification['paint']>;

const INITIAL_FIT_OPTIONS = {
  padding: MAP_FIT_PADDING,
  maxZoom: MAP_FIT_MAX_ZOOM,
} as const;

function PreviewLayers({ fc, sourceId }: { fc: FeatureCollection; sourceId: string }) {
  return (
    <Source id={sourceId} type="geojson" data={fc}>
      <Layer
        id={`${sourceId}-fill`}
        type="fill"
        paint={fillPaint}
        filter={FILTER_POLYGON}
      />
      <Layer
        id={`${sourceId}-poly-line`}
        type="line"
        paint={polygonOutlinePaint}
        filter={FILTER_POLYGON}
      />
      <Layer id={`${sourceId}-line`} type="line" paint={linePaint} filter={FILTER_LINE} />
      <Layer
        id={`${sourceId}-circle`}
        type="circle"
        paint={circlePaint}
        filter={FILTER_POINT}
      />
    </Source>
  );
}

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

  const initialBounds = useMemo(() => {
    if (!featureCollection) return undefined;
    const box = featureCollectionBounds(featureCollection);
    if (!box) return undefined;
    return boundsToLngLatBoundsLike(box);
  }, [featureCollection]);

  const fitWhenReady = useCallback(() => {
    const map = mapRef.current?.getMap();
    if (!map || !featureCollection) return;

    const runFit = () => fitMapToFeatureCollection(map, featureCollection);

    if (map.isStyleLoaded()) {
      runFit();
      return;
    }

    map.once('load', runFit);
  }, [featureCollection]);

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
  }, [featureCollection]);

  return (
    <div className="flex h-full min-h-[280px] flex-col rounded-xl border border-slate-200 bg-white shadow-sm">
      {featureCollection ? (
        <MapView
          ref={mapRef}
          className="overflow-hidden rounded-xl"
          height={height}
          bounds={initialBounds}
          fitBoundsOptions={INITIAL_FIT_OPTIONS}
          onLoad={fitWhenReady}
        >
          <PreviewLayers fc={featureCollection} sourceId={sourceId} />
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
