import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import type { ProjectDetailRead } from '../../api/client';
import { GeoJsonUploadZone } from '../project-upload/GeoJsonUploadZone';
import { PhotoUploadZone } from '../project-upload/PhotoUploadZone';
import { RouteUploadStatus } from './RouteUploadStatus';
import { useUploadGuard } from './useUploadGuard';

export function UploadDrawer({
  open,
  project,
  onRefresh,
  onUploadsBusyChange,
  onMergeMapData,
}: {
  open: boolean;
  project: ProjectDetailRead;
  onRefresh: () => Promise<void>;
  onUploadsBusyChange?: (busy: boolean) => void;
  onMergeMapData: (added: import('geojson').FeatureCollection) => void;
}) {
  const navigate = useNavigate();
  const [photosBusy, setPhotosBusy] = useState(false);
  const [geoBusy, setGeoBusy] = useState(false);

  const refresh = useCallback(async () => {
    await onRefresh();
  }, [onRefresh]);

  const routeReady = project.geojson_status === 'ready';
  const uploadsBusy = photosBusy || geoBusy;

  useUploadGuard(uploadsBusy, onUploadsBusyChange);

  return (
    <aside
      className={`flex shrink-0 flex-col overflow-hidden border-r border-slate-200 bg-slate-50 transition-[width] duration-300 ease-out ${
        open ? 'w-80' : 'w-0 border-r-0'
      }`}
      aria-hidden={!open}
    >
      <div
        className={`flex h-full w-80 flex-col gap-4 overflow-y-auto p-4 ${
          open ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
      >
        <GeoJsonUploadZone
          projectId={project.id}
          geojsonStatus={project.geojson_status}
          assets={project.assets}
          onRefresh={refresh}
          onMapData={onMergeMapData}
          onUploadingChange={setGeoBusy}
        />

        <PhotoUploadZone
          projectId={project.id}
          onRefresh={refresh}
          onUploadingChange={setPhotosBusy}
        />

        <footer className="mt-auto rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-3">
            <p className="text-xs text-slate-600">
              <RouteUploadStatus
                routeReady={routeReady}
                uploadsBusy={uploadsBusy}
                assets={project.assets}
                variant="footer"
              />
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={uploadsBusy}
                onClick={() => {
                  if (!uploadsBusy) navigate('/');
                }}
                title={
                  uploadsBusy
                    ? 'Wait for uploads to finish before leaving.'
                    : undefined
                }
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
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
    </aside>
  );
}
