import { useState } from 'react';
import { Link } from 'react-router-dom';

import type { ProjectDetailRead } from '../../api/client';
import { ProjectMapView } from '../project-map/ProjectMapView';
import { UploadMapPreview } from '../project-upload/UploadMapPreview';
import { ProjectPhotoDashboard } from './ProjectPhotoDashboard';
import { ProjectSummaryBar } from './ProjectSummaryBar';
import { UploadDrawer } from './UploadDrawer';
import { useProjectMapGeojson } from './useProjectMapGeojson';

export function ProjectDetailLayout({
  project,
  uploadsBusy,
  onRefresh,
  onUploadsBusyChange,
}: {
  project: ProjectDetailRead;
  uploadsBusy: boolean;
  onRefresh: () => Promise<void>;
  onUploadsBusyChange: (busy: boolean) => void;
}) {
  const [uploadDrawerOpen, setUploadDrawerOpen] = useState(true);
  const routeReady = project.geojson_status === 'ready';
  const { mapData, mergeMapData } = useProjectMapGeojson(project.id, project.geojson_status);

  return (
    <>
      <ProjectSummaryBar
        project={project}
        uploadDrawerOpen={uploadDrawerOpen}
        onToggleUploadDrawer={() => setUploadDrawerOpen((o) => !o)}
        uploadsBusy={uploadsBusy}
        onNameSaved={onRefresh}
      />

      <div className="flex min-h-[calc(100vh-8rem)] flex-1 flex-col lg:min-h-[calc(100vh-10rem)]">
        <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
          <UploadDrawer
            open={uploadDrawerOpen}
            project={project}
            onRefresh={onRefresh}
            onUploadsBusyChange={onUploadsBusyChange}
            onMergeMapData={mergeMapData}
          />

          <div className="flex min-h-0 min-w-0 flex-[2] flex-col border-b border-slate-200 lg:border-b-0 lg:border-r">
            <ProjectPhotoDashboard project={project} onRefresh={onRefresh} />
          </div>

          <div className="flex min-h-[480px] min-w-0 flex-1 flex-col">
            {routeReady && mapData ? (
              <ProjectMapView
                embedded
                project={project}
                mapData={mapData}
                onProjectRefresh={onRefresh}
              />
            ) : (
              <div className="h-full min-h-[480px] p-3">
                <UploadMapPreview featureCollection={mapData} height={480} />
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export function ProjectDetailHeader({
  uploadsBusy,
}: {
  uploadsBusy: boolean;
}) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="px-4 py-4 sm:px-6">
        <Link
          to="/"
          aria-disabled={uploadsBusy}
          onClick={(e) => {
            if (uploadsBusy) e.preventDefault();
          }}
          className={`text-sm font-medium text-slate-600 hover:text-slate-900 ${
            uploadsBusy ? 'pointer-events-none opacity-50' : ''
          }`}
        >
          ← Back to projects
        </Link>
      </div>
    </header>
  );
}
