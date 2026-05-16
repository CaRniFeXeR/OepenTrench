import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { FeatureCollection } from 'geojson';

import {
  readProjectGeojsonProjectsProjectIdGeojsonGet,
  type ProjectDetailRead,
} from '../../api/client';
import { GeoJsonUploadZone } from './GeoJsonUploadZone';
import { PhotoUploadZone } from './PhotoUploadZone';
import { UploadMapPreview } from './UploadMapPreview';
import {
  FCP_POLYGONS_GEOJSON_SUFFIX,
  TRENCHES_GEOJSON_SUFFIX,
  geojsonChecklistFromAssets,
} from './constants';
import {
  normalizeFeatureCollection,
  stripBlankFillColors,
} from '../../normalizeExampleGeojson';

function statusLabel(status: ProjectDetailRead['status']): string {
  switch (status) {
    case 'draft':
      return 'Draft';
    case 'analysing':
      return 'Analysing';
    case 'complete':
      return 'Complete';
    default:
      return status;
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString();
}

function mergeFeatureCollections(
  existing: FeatureCollection | null,
  added: FeatureCollection,
): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: [...(existing?.features ?? []), ...added.features],
  };
}

export function ProjectUploadPanel({
  project,
  onRefresh,
}: {
  project: ProjectDetailRead;
  onRefresh: () => Promise<void>;
}) {
  const navigate = useNavigate();
  const [mapData, setMapData] = useState<FeatureCollection | null>(null);
  const [photosBusy, setPhotosBusy] = useState(false);
  const [geoBusy, setGeoBusy] = useState(false);

  const refresh = useCallback(async () => {
    await onRefresh();
  }, [onRefresh]);

  const imageCount = project.assets.filter((a) => a.kind === 'image').length;
  const routeReady = project.geojson_status === 'ready';
  const uploadsBusy = photosBusy || geoBusy;
  const checklist = geojsonChecklistFromAssets(project.assets);

  useEffect(() => {
    if (project.geojson_status !== 'ready') return;

    let cancelled = false;
    void (async () => {
      const { data, error } = await readProjectGeojsonProjectsProjectIdGeojsonGet({
        path: { project_id: project.id },
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
  }, [project.id, project.geojson_status]);

  const handlePartialMapData = useCallback((added: FeatureCollection) => {
    setMapData((prev) => mergeFeatureCollections(prev, added));
  }, []);

  const missingGeojsonMessage = (): string => {
    if (routeReady) return '';
    const missing: string[] = [];
    if (!checklist.trenches) missing.push(TRENCHES_GEOJSON_SUFFIX);
    if (!checklist.fcpPolygons) missing.push(FCP_POLYGONS_GEOJSON_SUFFIX);
    if (missing.length === 2) {
      return 'Missing GeoJSON — upload Trenches and FCP_Polygons route files ⚠';
    }
    return `Still needed: ${missing.join(', ')} ⚠`;
  };

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
      <div className="flex flex-col gap-6 md:min-w-0">
        <header className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">{project.name}</h2>
          <dl className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
            <div>
              <dt className="text-slate-500">Region</dt>
              <dd className="font-medium text-slate-800">
                {project.region ?? 'Not set'}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Project date</dt>
              <dd className="font-medium text-slate-800">
                {formatDate(project.project_date)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Status</dt>
              <dd className="font-medium text-slate-800">{statusLabel(project.status)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Photos on server</dt>
              <dd className="font-medium text-slate-800">{imageCount}</dd>
            </div>
          </dl>
          <p className="mt-3 text-xs text-slate-500">
            Editing title, region, and date requires a project update API — not
            available yet.
          </p>
        </header>

        <GeoJsonUploadZone
          projectId={project.id}
          geojsonStatus={project.geojson_status}
          assets={project.assets}
          onRefresh={refresh}
          onMapData={handlePartialMapData}
          onUploadingChange={setGeoBusy}
        />

        <PhotoUploadZone
          projectId={project.id}
          onRefresh={refresh}
          onUploadingChange={setPhotosBusy}
        />

        <footer className="sticky bottom-4 rounded-xl border border-slate-200 bg-white p-4 shadow-md">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-slate-600">
              {routeReady && !uploadsBusy ? (
                <span className="font-medium text-emerald-700">Route files ready ✓</span>
              ) : uploadsBusy ? (
                <span>Upload in progress…</span>
              ) : (
                <span className="font-medium text-amber-800">{missingGeojsonMessage()}</span>
              )}
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => navigate('/')}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800 hover:bg-slate-50"
              >
                Save draft
              </button>
              <button
                type="button"
                disabled
                title="Analysis pipeline is not available yet."
                className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-45 hover:bg-slate-800 disabled:hover:bg-slate-900"
              >
                Save &amp; analyse
              </button>
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Files are stored when each upload completes. Save &amp; analyse will
            start the pipeline once that API is available.
          </p>
        </footer>
      </div>

      <div className="md:min-h-0 md:min-w-0">
        <UploadMapPreview featureCollection={mapData} height={480} />
      </div>
    </div>
  );
}
