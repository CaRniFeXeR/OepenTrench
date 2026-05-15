import { useCallback, useState } from 'react';
import type { FeatureCollection } from 'geojson';

import type { ProjectDetailRead } from '../../api/client';
import { GeoJsonUploadZone } from './GeoJsonUploadZone';
import { PhotoUploadZone } from './PhotoUploadZone';
import { UploadMapPreview } from './UploadMapPreview';

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

export function ProjectUploadPanel({
  project,
  onRefresh,
}: {
  project: ProjectDetailRead;
  onRefresh: () => Promise<void>;
}) {
  const [mapData, setMapData] = useState<FeatureCollection | null>(null);
  const [photosBusy, setPhotosBusy] = useState(false);
  const [geoBusy, setGeoBusy] = useState(false);

  const refresh = useCallback(async () => {
    await onRefresh();
  }, [onRefresh]);

  const imageCount = project.assets.filter((a) => a.kind === 'image').length;
  const hasGeoJsonAsset = project.assets.some((a) => a.kind === 'geojson');

  const uploadsBusy = photosBusy || geoBusy;
  const readyToAnalyse = hasGeoJsonAsset && !uploadsBusy;

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

        <PhotoUploadZone
          projectId={project.id}
          onRefresh={refresh}
          onUploadingChange={setPhotosBusy}
        />

        <GeoJsonUploadZone
          projectId={project.id}
          hasGeoJsonAsset={hasGeoJsonAsset}
          onRefresh={refresh}
          onMapData={setMapData}
          onUploadingChange={setGeoBusy}
        />

        <footer className="sticky bottom-4 rounded-xl border border-slate-200 bg-white p-4 shadow-md">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-slate-600">
              {readyToAnalyse ? (
                <span className="font-medium text-emerald-700">Ready to analyse ✓</span>
              ) : hasGeoJsonAsset ? (
                <span>
                  {uploadsBusy
                    ? 'Upload in progress…'
                    : 'GeoJSON present — add photos or continue.'}
                </span>
              ) : (
                <span className="font-medium text-amber-800">
                  Missing GeoJSON — map cannot be generated ⚠
                </span>
              )}
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled
                title="No draft-save API yet — uploads persist immediately."
                className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-500"
              >
                Save draft
              </button>
              <button
                type="button"
                disabled={!readyToAnalyse}
                title={
                  !hasGeoJsonAsset
                    ? 'Upload a GeoJSON route file first.'
                    : uploadsBusy
                      ? 'Wait for uploads to finish.'
                      : 'Analysis API is not wired yet.'
                }
                className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-45 hover:bg-slate-800 disabled:hover:bg-slate-900"
              >
                Save &amp; analyse
              </button>
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Files are stored when each upload completes. Save buttons are
            placeholders until PATCH and analyse endpoints exist.
          </p>
        </footer>
      </div>

      <div className="md:min-h-0 md:min-w-0">
        <UploadMapPreview featureCollection={mapData} height={480} />
      </div>
    </div>
  );
}
