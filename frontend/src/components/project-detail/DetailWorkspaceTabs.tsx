import type { FeatureCollection } from 'geojson';

import type { MapPhotoMarkerRead, ProjectDetailRead } from '../../api/client';
import type { DetailWorkspaceTab } from './layout/useProjectDetailLayoutState';
import { FilesTabPanel } from './FilesTabPanel';
import { ProjectPhotoDashboard } from './photo-dashboard/ProjectPhotoDashboard';

const TABS: { id: DetailWorkspaceTab; label: string }[] = [
  { id: 'files', label: 'Files' },
  { id: 'analysis', label: 'Analysis' },
];

export function DetailWorkspaceTabs({
  project,
  activeTab,
  onActiveTabChange,
  mapData,
  mapPhotos,
  selectedFcpId,
  onSelectedFcpIdChange,
  onRefresh,
  onUploadsBusyChange,
  onMergeMapData,
}: {
  project: ProjectDetailRead;
  activeTab: DetailWorkspaceTab;
  onActiveTabChange: (tab: DetailWorkspaceTab) => void;
  mapData: FeatureCollection | null;
  mapPhotos: MapPhotoMarkerRead[];
  selectedFcpId: string | null;
  onSelectedFcpIdChange: (fcpId: string | null) => void;
  onRefresh: () => Promise<void>;
  onUploadsBusyChange: (busy: boolean) => void;
  onMergeMapData: (added: FeatureCollection) => void;
}) {
  return (
    <aside className="flex min-h-0 min-w-0 flex-[2] flex-col border-b border-slate-200 bg-slate-50 lg:border-b-0 lg:border-r">
      <nav
        role="tablist"
        aria-label="Project workspace"
        className="flex shrink-0 border-b border-slate-200 bg-white"
      >
        {TABS.map((tab) => {
          const selected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => onActiveTabChange(tab.id)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition ${
                selected
                  ? 'border-b-2 border-violet-600 text-violet-700'
                  : 'border-b-2 border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </nav>

      <div className="min-h-0 flex-1 overflow-hidden" role="tabpanel">
        {activeTab === 'files' ? (
          <FilesTabPanel
            project={project}
            onRefresh={onRefresh}
            onUploadsBusyChange={onUploadsBusyChange}
            onMergeMapData={onMergeMapData}
          />
        ) : (
          <ProjectPhotoDashboard
            project={project}
            mapData={mapData}
            mapPhotos={mapPhotos}
            selectedFcpId={selectedFcpId}
            onSelectedFcpIdChange={onSelectedFcpIdChange}
            onRefresh={onRefresh}
          />
        )}
      </div>
    </aside>
  );
}
