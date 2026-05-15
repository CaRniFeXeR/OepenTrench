import { useEffect, useState } from 'react';
import { Layer, Source } from 'react-map-gl/maplibre';

import type { FeatureCollection } from 'geojson';
import type {
  CircleLayerSpecification,
  FillLayerSpecification,
  FilterSpecification,
  LineLayerSpecification,
} from '@maplibre/maplibre-gl-style-spec';

import { MapView } from '../components/MapView';
import { EXAMPLE_GEOJSON_DATASETS } from '../exampleGeojsonModuleUrls';
import {
  normalizeFeatureCollection,
  stripBlankFillColors,
} from '../normalizeExampleGeojson';

const FALLBACK_HEX_BY_INDEX = [
  '#6366f1',
  '#0ea5e9',
  '#14b8a6',
  '#f97316',
  '#a855f7',
] as const;

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

function DatasetOverlay({
  fallbackHex,
  featureCollection,
  sourceIdSuffix,
}: {
  fallbackHex: string;
  featureCollection: FeatureCollection;
  sourceIdSuffix: string;
}) {
  const fillPaint = {
    'fill-color': ['coalesce', ['get', 'fillColor'], fallbackHex],
    'fill-opacity': 0.4,
  } as NonNullable<FillLayerSpecification['paint']>;

  const polygonLinePaint = {
    'line-color': ['coalesce', ['get', 'fillColor'], fallbackHex],
    'line-width': 2,
  } as NonNullable<LineLayerSpecification['paint']>;

  const linePaint = {
    'line-color': ['coalesce', ['get', 'fillColor'], fallbackHex],
    'line-width': 3,
  } as NonNullable<LineLayerSpecification['paint']>;

  const circlePaint = {
    'circle-radius': 6,
    'circle-color': ['coalesce', ['get', 'fillColor'], fallbackHex],
    'circle-stroke-width': 1,
    'circle-stroke-color': '#1e293b',
  } as NonNullable<CircleLayerSpecification['paint']>;

  return (
    <Source
      id={`ex-src-${sourceIdSuffix}`}
      type="geojson"
      data={featureCollection}
    >
      <Layer
        id={`ex-${sourceIdSuffix}-fill`}
        type="fill"
        paint={fillPaint}
        filter={FILTER_POLYGON}
      />
      <Layer
        id={`ex-${sourceIdSuffix}-polygon-outline`}
        type="line"
        paint={polygonLinePaint}
        filter={FILTER_POLYGON}
      />
      <Layer
        id={`ex-${sourceIdSuffix}-line`}
        type="line"
        paint={linePaint}
        filter={FILTER_LINE}
      />
      <Layer
        id={`ex-${sourceIdSuffix}-circle`}
        type="circle"
        paint={circlePaint}
        filter={FILTER_POINT}
      />
    </Source>
  );
}

export function GeoJsonDemoPage() {
  const [loadedById, setLoadedById] = useState<
    Record<string, FeatureCollection>
  >({});
  const [failedById, setFailedById] = useState<Record<string, string>>({});

  useEffect(() => {
    let cancelled = false;

    async function fetchOne(ds: (typeof EXAMPLE_GEOJSON_DATASETS)[number]) {
      try {
        const response = await fetch(ds.url);
        if (!response.ok) {
          throw new Error(`${response.status} ${response.statusText}`);
        }

        const json: unknown = await response.json();

        const featureCollection = stripBlankFillColors(
          normalizeFeatureCollection(json),
        );
        if (cancelled) return;
        setLoadedById((prev) => ({ ...prev, [ds.id]: featureCollection }));
      } catch (err) {
        if (cancelled) return;

        const message = err instanceof Error ? err.message : String(err);

        setFailedById((prev) => ({
          ...prev,
          [ds.id]: message,
        }));
      }
    }

    void Promise.all(
      EXAMPLE_GEOJSON_DATASETS.map(async (dataset) =>
        fetchOne(dataset),
      ),
    );

    return () => {
      cancelled = true;
    };
  }, []);

  const completedCount =
    Object.keys(loadedById).length + Object.keys(failedById).length;

  const loading = completedCount < EXAMPLE_GEOJSON_DATASETS.length;

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <h1 className="text-2xl font-semibold text-slate-900">
            GeoJSON demo
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Example trench data from{' '}
            <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">
              data/example_geojson
            </code>
          </p>
          <ol className="mt-4 list-inside list-decimal text-sm text-slate-700">
            {EXAMPLE_GEOJSON_DATASETS.map((dataset, index) => {
              const fallback =
                FALLBACK_HEX_BY_INDEX[index % FALLBACK_HEX_BY_INDEX.length];
              let statusChip: string;
              if (loadedById[dataset.id]) {
                statusChip = `${loadedById[dataset.id]!.features.length} features`;
              } else if (failedById[dataset.id]) {
                statusChip = 'error';
              } else {
                statusChip = '…';
              }

              return (
                <li key={dataset.id}>
                  <span className="font-medium">{dataset.label}</span>
                  <span className="text-slate-500">
                    {' '}
                    — {statusChip}; fallback&nbsp;
                  </span>
                  <span
                    className="inline-block translate-y-[2px] rounded-sm border border-slate-300 px-[6px] py-[1px] align-middle"
                    style={{
                      backgroundColor: fallback,
                    }}
                    aria-label={`Fallback color ${fallback}`}
                  >
                    {' '}
                  </span>{' '}
                  <span className="font-mono text-xs text-slate-600">
                    {fallback}
                  </span>
                </li>
              );
            })}
          </ol>
          {loading && (
            <p className="mt-3 text-sm text-slate-500">Loading GeoJSON…</p>
          )}
          {Object.keys(failedById).length > 0 && (
            <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              <p className="font-medium">Some files failed to load</p>
              <ul className="mt-2 list-inside list-disc">
                {Object.entries(failedById).map(([id, message]) => (
                  <li key={id}>
                    <span className="font-mono">{id}</span>: {message}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <MapView
          className="w-full overflow-hidden rounded-lg border border-slate-200"
          height={640}
        >
          {EXAMPLE_GEOJSON_DATASETS.map((dataset, index) => {
            const data = loadedById[dataset.id];
            if (!data) return null;
            return (
              <DatasetOverlay
                key={dataset.id}
                sourceIdSuffix={dataset.id}
                featureCollection={data}
                fallbackHex={
                  FALLBACK_HEX_BY_INDEX[index % FALLBACK_HEX_BY_INDEX.length]
                }
              />
            );
          })}
        </MapView>
      </main>
    </div>
  );
}
