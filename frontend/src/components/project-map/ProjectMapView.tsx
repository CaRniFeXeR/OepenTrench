import { useMemo, useRef } from 'react';
import type { FeatureCollection } from 'geojson';
import type { MapRef } from 'react-map-gl/maplibre';

import type { MapPhotoMarkerRead, ProjectDetailRead } from '../../api/client';
import { imageAssets } from '../project-images/projectImageListUtils';
import { MapView } from '../map/MapView';
import { useMapFitToFeatureCollection } from '../map/useMapFitToFeatureCollection';
import { FcpSummaryPanel } from './FcpSummaryPanel';
import { MapDetailColumn } from './MapDetailColumn';
import { MapOverlayPanels } from './MapOverlayPanels';
import { ProjectMapLayers } from './ProjectMapLayers';
import { TrenchImageDetailPanel } from './TrenchImageDetailPanel';
import { buildCoverageCompartmentCollection } from './coverageCompartmentUtils';
import { useFcpCoverage } from './useFcpCoverage';
import { useProjectMapData } from './useProjectMapData';
import { useProjectMapNavigation } from './useProjectMapNavigation';

export function ProjectMapView({
  project,
  mapData,
  onProjectRefresh,
  embedded = false,
  mapPhotos: mapPhotosProp,
  mapPhotosLoading = false,
  selectedFcpId,
  onSelectedFcpIdChange,
  mapPhotosRefreshKey = 0,
}: {
  project: ProjectDetailRead;
  mapData: FeatureCollection;
  onProjectRefresh: () => Promise<void>;
  embedded?: boolean;
  mapPhotos?: MapPhotoMarkerRead[];
  mapPhotosLoading?: boolean;
  selectedFcpId?: string | null;
  onSelectedFcpIdChange?: (fcpId: string | null) => void;
  mapPhotosRefreshKey?: number;
}) {
  const mapRef = useRef<MapRef | null>(null);
  const projectImageAssets = useMemo(() => imageAssets(project.assets), [project.assets]);
  const imageCount = projectImageAssets.length;

  const internalMapData = useProjectMapData(project.id, imageCount);
  const mapPhotos = mapPhotosProp ?? internalMapData.mapPhotos;
  const photosLoading = mapPhotosProp != null ? mapPhotosLoading : internalMapData.loading;

  const routeReady = project.geojson_status === 'ready';
  const { coverage, loading: coverageLoading, error: coverageError } = useFcpCoverage(
    project.id,
    selectedFcpId ?? null,
    routeReady,
    mapPhotosRefreshKey,
  );
  const coverageCompartments = useMemo(
    () =>
      coverage
        ? buildCoverageCompartmentCollection(coverage.compartments)
        : null,
    [coverage],
  );

  const navigation = useProjectMapNavigation({
    mapRef,
    mapData,
    mapPhotos,
    imageAssets: projectImageAssets,
    selectedFcpId,
    onSelectedFcpIdChange,
  });

  const { initialBounds, fitBoundsOptions, onMapLoad } =
    useMapFitToFeatureCollection(mapRef, mapData);

  const {
    level,
    setLevel,
    selectedFcpId: resolvedSelectedFcpId,
    fcpPolygons,
    trenches,
    photoMarkers,
    navigablePhotos,
    fcpPhotos,
    fcpLabel,
    fcpCode,
    highlightedPhotoIdResolved,
    activeAsset,
    photoIndex,
    detailOpen,
    goToProject,
    goToPhoto,
    handleMapClick,
    stepPhoto,
    reviewQueueMode,
    startWarningReview,
    warningReviewCount,
  } = navigation;

  const coverageSummary = useMemo(() => {
    if (!coverage || !resolvedSelectedFcpId) return null;
    return (
      coverage.summaries.find((s) => s.fcp_id === resolvedSelectedFcpId) ?? null
    );
  }, [coverage, resolvedSelectedFcpId]);

  const handleReviewSaved = async () => {
    await onProjectRefresh();
  };

  return (
    <div
      className={`flex min-h-[480px] flex-1 flex-col ${embedded ? 'min-h-0' : 'lg:flex-row lg:min-h-0'}`}
    >
      <div
        className={`relative min-h-[480px] flex-1 overflow-hidden bg-slate-100 ${embedded ? 'min-h-0' : 'lg:min-h-0'}`}
      >
        <MapView
          ref={mapRef}
          className="h-full w-full"
          bounds={initialBounds}
          fitBoundsOptions={fitBoundsOptions}
          onLoad={onMapLoad}
          onClick={handleMapClick}
        >
          <ProjectMapLayers
            trenches={trenches}
            fcpPolygons={fcpPolygons}
            photoMarkers={photoMarkers}
            coverageCompartments={coverageCompartments}
            selectedFcpId={resolvedSelectedFcpId}
          />
        </MapView>

        {(embedded || level === 'project') && (
          <MapOverlayPanels
            projectName={project.name}
            fcpCount={fcpPolygons.features.length}
            photos={mapPhotos}
            selectedFcpId={resolvedSelectedFcpId}
            coverageSummary={coverageSummary}
            coverageLoading={coverageLoading}
          />
        )}

        {(photosLoading || coverageLoading) && (
          <div className="pointer-events-none absolute left-1/2 top-3 z-10 -translate-x-1/2 rounded-full bg-white/90 px-3 py-1 text-xs text-slate-600 shadow">
            {coverageLoading ? 'Calculating trench coverage…' : 'Loading photo markers…'}
          </div>
        )}

        {coverageError && resolvedSelectedFcpId && (
          <div className="pointer-events-none absolute left-1/2 top-10 z-10 -translate-x-1/2 rounded-full bg-red-50 px-3 py-1 text-xs text-red-700 shadow">
            {coverageError}
          </div>
        )}
      </div>

      {!embedded && (
        <MapDetailColumn open={detailOpen}>
          {level === 'fcp' && resolvedSelectedFcpId && (
            <FcpSummaryPanel
              fcpLabel={fcpLabel}
              fcpCode={fcpCode}
              projectName={project.name}
              photos={fcpPhotos}
              highlightedPhotoId={highlightedPhotoIdResolved}
              warningReviewCount={warningReviewCount}
              onBack={goToProject}
              onPrevPhoto={() => stepPhoto(-1)}
              onNextPhoto={() => stepPhoto(1)}
              onOpenPhoto={() => {
                if (highlightedPhotoIdResolved) {
                  goToPhoto(highlightedPhotoIdResolved, resolvedSelectedFcpId);
                }
              }}
              onStartWarningReview={() => startWarningReview(resolvedSelectedFcpId)}
            />
          )}
          {level === 'photo' &&
            activeAsset &&
            highlightedPhotoIdResolved &&
            photoIndex >= 0 && (
              <TrenchImageDetailPanel
                projectId={project.id}
                asset={activeAsset}
                fcpCode={fcpCode}
                photoIndex={photoIndex}
                photoTotal={navigablePhotos.length}
                reviewQueueMode={reviewQueueMode}
                onBack={() => {
                  setLevel('fcp');
                }}
                onPrev={() => stepPhoto(-1)}
                onNext={() => stepPhoto(1)}
                onReviewSaved={handleReviewSaved}
              />
            )}
        </MapDetailColumn>
      )}
    </div>
  );
}

