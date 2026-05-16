import { useEffect, useState } from 'react';
import { Layer, Source } from 'react-map-gl/maplibre';

import type { FeatureCollection } from 'geojson';
import type {
  CircleLayerSpecification,
  FillLayerSpecification,
  FilterSpecification,
  LineLayerSpecification,
} from '@maplibre/maplibre-gl-style-spec';

import { MapView } from '../components/map/MapView';
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

export type GeometryLayerVisibility = {
  polygonFill: boolean;
  polygonOutline: boolean;
  lines: boolean;
  points: boolean;
};

function DatasetOverlay({
  fallbackHex,
  featureCollection,
  layerVisibility,
  sourceIdSuffix,
}: {
  fallbackHex: string;
  featureCollection: FeatureCollection;
  layerVisibility: GeometryLayerVisibility;
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
        layout={{
          visibility: layerVisibility.polygonFill ? 'visible' : 'none',
        }}
        paint={fillPaint}
        filter={FILTER_POLYGON}
      />
      <Layer
        id={`ex-${sourceIdSuffix}-polygon-outline`}
        type="line"
        layout={{
          visibility: layerVisibility.polygonOutline ? 'visible' : 'none',
        }}
        paint={polygonLinePaint}
        filter={FILTER_POLYGON}
      />
      <Layer
        id={`ex-${sourceIdSuffix}-line`}
        type="line"
        layout={{
          visibility: layerVisibility.lines ? 'visible' : 'none',
        }}
        paint={linePaint}
        filter={FILTER_LINE}
      />
      <Layer
        id={`ex-${sourceIdSuffix}-circle`}
        type="circle"
        layout={{
          visibility: layerVisibility.points ? 'visible' : 'none',
        }}
        paint={circlePaint}
        filter={FILTER_POINT}
      />
    </Source>
  );
}

function defaultDatasetVisibility(): Record<string, boolean> {
  return Object.fromEntries(
    EXAMPLE_GEOJSON_DATASETS.map((ds) => [ds.id, true]),
  );
}

const INITIAL_GEOMETRY_VISIBILITY: GeometryLayerVisibility = {
  polygonFill: true,
  polygonOutline: true,
  lines: true,
  points: true,
};

export function GeoJsonDemoPage() {
  const [loadedById, setLoadedById] = useState<
    Record<string, FeatureCollection>
  >({});
  const [failedById, setFailedById] = useState<Record<string, string>>({});
  const [geometryVisibility, setGeometryVisibility] =
    useState<GeometryLayerVisibility>(INITIAL_GEOMETRY_VISIBILITY);
  const [datasetVisible, setDatasetVisible] = useState<
    Record<string, boolean>
  >(() => defaultDatasetVisibility());

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

  const allGeometryLayersOn =
    geometryVisibility.polygonFill &&
    geometryVisibility.polygonOutline &&
    geometryVisibility.lines &&
    geometryVisibility.points;

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
        <div className="relative">
          <MapView
            className="w-full overflow-hidden rounded-lg border border-slate-200"
            height={640}
          >
            {EXAMPLE_GEOJSON_DATASETS.map((dataset, index) => {
              const data = loadedById[dataset.id];
              if (!data || datasetVisible[dataset.id] === false) {
                return null;
              }
              return (
                <DatasetOverlay
                  key={dataset.id}
                  sourceIdSuffix={dataset.id}
                  featureCollection={data}
                  layerVisibility={geometryVisibility}
                  fallbackHex={
                    FALLBACK_HEX_BY_INDEX[index % FALLBACK_HEX_BY_INDEX.length]
                  }
                />
              );
            })}
          </MapView>

          <div className="absolute left-4 top-4 z-10 max-w-[min(20rem,calc(100%-2rem))] rounded-lg border border-slate-200 bg-white/95 p-4 text-sm shadow-sm backdrop-blur-sm">
            <p className="font-medium text-slate-900">
              Layers (GeoJSON structure)
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Toggle how each geometry type is drawn on the map.
            </p>
            <div className="mt-3 space-y-2">
              <label className="flex cursor-pointer items-start gap-2 text-slate-700">
                <input
                  type="checkbox"
                  checked={geometryVisibility.polygonFill}
                  onChange={(e) =>
                    setGeometryVisibility((v) => ({
                      ...v,
                      polygonFill: e.target.checked,
                    }))
                  }
                  className="mt-1"
                />
                <span>
                  <span className="font-medium">Polygon / MultiPolygon</span>{' '}
                  <span className="block text-xs text-slate-500">
                    Interior fill (MapLibre <code className="text-slate-600">fill</code>{' '}
                    layer)
                  </span>
                </span>
              </label>
              <label className="flex cursor-pointer items-start gap-2 text-slate-700">
                <input
                  type="checkbox"
                  checked={geometryVisibility.polygonOutline}
                  onChange={(e) =>
                    setGeometryVisibility((v) => ({
                      ...v,
                      polygonOutline: e.target.checked,
                    }))
                  }
                  className="mt-1"
                />
                <span>
                  <span className="font-medium">
                    Polygon / MultiPolygon outline
                  </span>{' '}
                  <span className="block text-xs text-slate-500">
                    Boundary stroke (same geometries,{' '}
                    <code className="text-slate-600">line</code> layer)
                  </span>
                </span>
              </label>
              <label className="flex cursor-pointer items-start gap-2 text-slate-700">
                <input
                  type="checkbox"
                  checked={geometryVisibility.lines}
                  onChange={(e) =>
                    setGeometryVisibility((v) => ({
                      ...v,
                      lines: e.target.checked,
                    }))
                  }
                  className="mt-1"
                />
                <span>
                  <span className="font-medium">
                    LineString / MultiLineString
                  </span>{' '}
                  <span className="block text-xs text-slate-500">
                    <code className="text-slate-600">line</code> layer
                  </span>
                </span>
              </label>
              <label className="flex cursor-pointer items-start gap-2 text-slate-700">
                <input
                  type="checkbox"
                  checked={geometryVisibility.points}
                  onChange={(e) =>
                    setGeometryVisibility((v) => ({
                      ...v,
                      points: e.target.checked,
                    }))
                  }
                  className="mt-1"
                />
                <span>
                  <span className="font-medium">Point</span>{' '}
                  <span className="block text-xs text-slate-500">
                    <code className="text-slate-600">circle</code> layer
                  </span>
                </span>
              </label>
            </div>

            {!allGeometryLayersOn && (
              <div className="mt-3 border-t border-slate-100 pt-3">
                <button
                  type="button"
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
                  onClick={() =>
                    setGeometryVisibility({ ...INITIAL_GEOMETRY_VISIBILITY })
                  }
                >
                  All geometry layers on
                </button>
              </div>
            )}

            <div className="mt-5 border-t border-slate-200 pt-4">
              <p className="font-medium text-slate-900">Example files</p>
              <p className="mt-1 text-xs text-slate-500">
                Show or hide entire FeatureCollections loaded from{' '}
                <code className="text-slate-600">data/example_geojson</code>.
              </p>
              <div className="mt-3 space-y-2">
                {EXAMPLE_GEOJSON_DATASETS.map((dataset) => {
                  const loaded = Boolean(loadedById[dataset.id]);
                  const fileShown = datasetVisible[dataset.id] ?? true;

                  return (
                    <label
                      key={dataset.id}
                      className={
                        loaded
                          ? 'flex cursor-pointer items-start gap-2 text-slate-700'
                          : 'flex cursor-not-allowed items-start gap-2 text-slate-400'
                      }
                    >
                      <input
                        type="checkbox"
                        checked={fileShown}
                        disabled={!loaded}
                        onChange={(e) =>
                          setDatasetVisible((prev) => ({
                            ...prev,
                            [dataset.id]: e.target.checked,
                          }))
                        }
                        className="mt-1 disabled:opacity-50"
                      />
                      <span className="leading-snug">{dataset.label}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
