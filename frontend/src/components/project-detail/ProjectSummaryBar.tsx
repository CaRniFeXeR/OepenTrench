import type { ProjectDetailRead } from '../../api/client';
import {
  formatProjectDate,
  photoCountLabel,
  statusChipClass,
  statusLabel,
} from '../../lib/projectFormatters';
import { EditableProjectName } from '../project-upload/EditableProjectName';
import { missingGeojsonMessage } from './routeStatus';

export function ProjectSummaryBar({
  project,
  uploadDrawerOpen,
  onToggleUploadDrawer,
  uploadsBusy,
  onNameSaved,
}: {
  project: ProjectDetailRead;
  uploadDrawerOpen: boolean;
  onToggleUploadDrawer: () => void;
  uploadsBusy: boolean;
  onNameSaved: () => Promise<void>;
}) {
  const imageCount = project.assets.filter((a) => a.kind === 'image').length;
  const routeReady = project.geojson_status === 'ready';
  const statusMessage = missingGeojsonMessage(routeReady, project.assets);

  return (
    <div className="border-b border-slate-200 bg-white px-4 py-3 sm:px-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <EditableProjectName
            projectId={project.id}
            name={project.name}
            onSaved={onNameSaved}
          />
          <dl className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-600">
            <div>
              <dt className="inline text-slate-500 after:content-[':']">Region</dt>{' '}
              <dd className="inline font-medium text-slate-800">
                {project.region ?? 'Not set'}
              </dd>
            </div>
            <div>
              <dt className="inline text-slate-500 after:content-[':']">Project date</dt>{' '}
              <dd className="inline font-medium text-slate-800">
                {formatProjectDate(project.project_date)}
              </dd>
            </div>
            <div>
              <dt className="inline text-slate-500 after:content-[':']">Status</dt>{' '}
              <dd className="inline font-medium text-slate-800">
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${statusChipClass(project.status)}`}
                >
                  {statusLabel(project.status)}
                </span>
              </dd>
            </div>
            <div>
              <dt className="inline text-slate-500 after:content-[':']">Photos</dt>{' '}
              <dd className="inline font-medium text-slate-800">
                {photoCountLabel(imageCount)}
              </dd>
            </div>
          </dl>
          <p className="mt-1 text-xs text-slate-500">
            Double-click the project name to rename.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {!routeReady && !uploadsBusy && statusMessage && (
            <span className="max-w-xs text-xs font-medium text-amber-800">{statusMessage}</span>
          )}
          {routeReady && !uploadsBusy && (
            <span className="text-xs font-medium text-emerald-700">Route ready ✓</span>
          )}
          {uploadsBusy && (
            <span className="text-xs text-slate-600">Upload in progress…</span>
          )}
          <button
            type="button"
            onClick={onToggleUploadDrawer}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-50"
            aria-expanded={uploadDrawerOpen}
          >
            {uploadDrawerOpen ? 'Hide uploads' : 'Show uploads'}
            <span className="ml-1" aria-hidden>
              {uploadDrawerOpen ? '◀' : '▶'}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
