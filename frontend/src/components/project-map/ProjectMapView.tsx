import { useMemo, useRef } from 'react';
import type { FeatureCollection } from 'geojson';
import type { MapRef } from 'react-map-gl/maplibre';

import type {
  FcpCoverageRead,
  MapPhotoMarkerRead,
  ProjectDetailRead,
} from '../../api/client';
import { imageAssets } from '../project-images/projectImageListUtils';
import { MapView } from '../map/MapView';
import { useMapFitToFeatureCollection } from '../map/useMapFitToFeatureCollection';
import { FcpSummaryPanel } from './FcpSummaryPanel';
import { MapDetailColumn } from './MapDetailColumn';
import { MapOverlayPanels } from './MapOverlayPanels';
import { ProjectMapLayers } from './ProjectMapLayers';
import { TrenchImageDetailPanel } from './TrenchImageDetailPanel';
import { buildCoverageCompartmentCollection } from './coverageCompartmentUtils';
import { useProjectMapData } from './useProjectMapData';
import { useProjectMapNavigation } from './useProjectMapNavigation';

export function ProjectMapView({
  project,
  mapData,
  onProjectRefresh,
  embedded = false,
  className,
  mapPhotos: mapPhotosProp,
  mapPhotosLoading = false,
  selectedFcpId,
  onSelectedFcpIdChange,
  coverage = null,
  coverageLoading = false,
}: {
  project: ProjectDetailRead;
  mapData: FeatureCollection;
  onProjectRefresh: () => Promise<void>;
  embedded?: boolean;
  className?: string;
  mapPhotos?: MapPhotoMarkerRead[];
  mapPhotosLoading?: boolean;
  selectedFcpId?: string | null;
  onSelectedFcpIdChange?: (fcpId: string | null) => void;
  coverage?: FcpCoverageRead | null;
  coverageLoading?: boolean;
}) {
  const mapRef = useRef<MapRef | null>(null);
  const projectImageAssets = useMemo(() => imageAssets(project.assets), [project.assets]);
  const imageCount = projectImageAssets.length;

  const internalMapData = useProjectMapData(project.id, imageCount);
  const mapPhotos = mapPhotosProp ?? internalMapData.mapPhotos;
  const photosLoading = mapPhotosProp != null ? mapPhotosLoading : internalMapData.loading;

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

  const coverageCompartments = useMemo(() => {
    if (!coverage || !resolvedSelectedFcpId) return null;
    const filtered = coverage.compartments.filter(
      (comp) => comp.fcp_id === resolvedSelectedFcpId,
    );
    return filtered.length > 0 ? buildCoverageCompartmentCollection(filtered) : null;
  }, [coverage, resolvedSelectedFcpId]);

  const handleReviewSaved = async () => {
    await onProjectRefresh();
  };

  const rootClassName = [
    'flex min-h-[480px] flex-1 flex-col',
    embedded ? 'min-h-0' : 'lg:flex-row lg:min-h-0',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={rootClassName}>
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

        {photosLoading && (
          <div className="pointer-events-none absolute left-1/2 top-3 z-10 -translate-x-1/2 rounded-full bg-white/90 px-3 py-1 text-xs text-slate-600 shadow">
            Loading photo markers…
          </div>
        )}

        {coverageLoading && (
          <div className="pointer-events-none absolute left-1/2 top-10 z-10 -translate-x-1/2 rounded-full bg-white/90 px-3 py-1 text-xs text-slate-600 shadow">
            Calculating trench coverage…
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

