import type { ProjectDetailRead } from '../../../api/client';
import { imageAssets } from '../../project-images/projectImageListUtils';
import { useProjectMapData } from '../../project-map/useProjectMapData';
import { ProjectMapView } from '../../project-map/ProjectMapView';
import { UploadMapPreview } from '../../project-upload/UploadMapPreview';
import { DetailWorkspaceTabs } from '../DetailWorkspaceTabs';
import { ProjectSummaryBar } from '../ProjectSummaryBar';
import { TrenchCoverageOverview } from '../TrenchCoverageOverview';
import { useProjectFcpCoverage } from '../useProjectFcpCoverage';
import { useProjectMapGeojson } from '../useProjectMapGeojson';
import { useProjectDetailLayoutState } from './useProjectDetailLayoutState';

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
  const {
    activeTab,
    setActiveTab,
    selectedFcpId,
    setSelectedFcpId,
    mapPhotosRefreshKey,
    handleRefresh,
  } = useProjectDetailLayoutState(onRefresh);

  const routeReady = project.geojson_status === 'ready';
  const { mapData, mergeMapData } = useProjectMapGeojson(project.id, project.geojson_status);
  const imageCount = imageAssets(project.assets).length;
  const { mapPhotos, loading: mapPhotosLoading } = useProjectMapData(
    project.id,
    imageCount,
    mapPhotosRefreshKey,
  );
  const {
    coverage,
    loading: coverageLoading,
    calculating: coverageCalculating,
    error: coverageError,
    calculateCoverage,
  } = useProjectFcpCoverage(project.id, routeReady, mapPhotosRefreshKey);

  return (
    <>
      <ProjectSummaryBar
        project={project}
        uploadsBusy={uploadsBusy}
        onNameSaved={handleRefresh}
      />

      <div className="flex min-h-[calc(100vh-8rem)] flex-1 flex-col lg:min-h-[calc(100vh-10rem)]">
        <div className="flex min-h-0 flex-1 flex-col lg:flex-row lg:items-start">
          <DetailWorkspaceTabs
            project={project}
            activeTab={activeTab}
            onActiveTabChange={setActiveTab}
            mapData={mapData}
            mapPhotos={mapPhotos}
            selectedFcpId={selectedFcpId}
            onSelectedFcpIdChange={setSelectedFcpId}
            onRefresh={handleRefresh}
            onUploadsBusyChange={onUploadsBusyChange}
            onMergeMapData={mergeMapData}
            routeReady={routeReady}
            coverage={coverage}
            coverageLoading={coverageLoading}
          />

          <div className="print:hidden flex min-h-[480px] min-w-0 flex-1 flex-col lg:h-auto lg:self-start">
            {routeReady && mapData ? (
              <>
                <ProjectMapView
                  embedded
                  className="h-[480px] min-h-[480px] shrink-0 flex-none"
                  project={project}
                  mapData={mapData}
                  mapPhotos={mapPhotos}
                  mapPhotosLoading={mapPhotosLoading}
                  selectedFcpId={selectedFcpId}
                  onSelectedFcpIdChange={setSelectedFcpId}
                  onProjectRefresh={handleRefresh}
                  coverage={coverage}
                  coverageLoading={coverageCalculating}
                />
                <TrenchCoverageOverview
                  routeReady={routeReady}
                  coverage={coverage}
                  loading={coverageLoading}
                  calculating={coverageCalculating}
                  error={coverageError}
                  selectedFcpId={selectedFcpId}
                  onCalculate={calculateCoverage}
                />
              </>
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
