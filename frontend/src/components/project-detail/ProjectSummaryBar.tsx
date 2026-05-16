import type { ProjectDetailRead } from '../../api/client';
import {
  formatProjectDate,
  photoCountLabel,
  statusChipClass,
  statusLabel,
} from '../../helpers/projectFormatters';
import { imageAssets } from '../project-images/projectImageListUtils';
import { EditableProjectName } from '../project-upload/EditableProjectName';
import { RouteUploadStatus } from './RouteUploadStatus';

export function ProjectSummaryBar({
  project,
  uploadsBusy,
  onNameSaved,
}: {
  project: ProjectDetailRead;
  uploadsBusy: boolean;
  onNameSaved: () => Promise<void>;
}) {
  const imageCount = imageAssets(project.assets).length;
  const routeReady = project.geojson_status === 'ready';

  return (
    <div className="print:hidden border-b border-slate-200 bg-white px-4 py-3 sm:px-6">
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

        <RouteUploadStatus
          routeReady={routeReady}
          uploadsBusy={uploadsBusy}
          assets={project.assets}
          variant="inline"
        />
      </div>
    </div>
  );
}
