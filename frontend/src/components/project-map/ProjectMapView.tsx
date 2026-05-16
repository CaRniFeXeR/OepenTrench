import { useMemo, useRef, useState } from 'react';
import type { MapRef } from 'react-map-gl/maplibre';
import type { FeatureCollection } from 'geojson';

import type { ProjectDetailRead } from '../../api/client';
import { MapView } from '../map/MapView';
import { useMapFitToFeatureCollection } from '../map/useMapFitToFeatureCollection';
import { FcpSummaryPanel } from './FcpSummaryPanel';
import { MapDetailColumn } from './MapDetailColumn';
import { MapOverlayPanels } from './MapOverlayPanels';
import { ProjectMapLayers } from './ProjectMapLayers';
import { TrenchImageDetailPanel } from './TrenchImageDetailPanel';
import { useProjectMapData } from './useProjectMapData';
import { useProjectMapNavigation } from './useProjectMapNavigation';

export function ProjectMapView({
  project,
  mapData,
  onProjectRefresh,
  embedded = false,
}: {
  project: ProjectDetailRead;
  mapData: FeatureCollection;
  onProjectRefresh: () => Promise<void>;
  embedded?: boolean;
}) {
  const mapRef = useRef<MapRef | null>(null);
  const [mapPhotosRefreshKey, setMapPhotosRefreshKey] = useState(0);
  const imageCount = project.assets.filter((a) => a.kind === 'image').length;
  const imageAssets = useMemo(
    () => project.assets.filter((a) => a.kind === 'image'),
    [project.assets],
  );

  const { mapPhotos, loading: photosLoading } = useProjectMapData(
    project.id,
    imageCount,
    mapPhotosRefreshKey,
  );

  const navigation = useProjectMapNavigation({
    mapRef,
    mapData,
    mapPhotos,
    imageAssets,
  });

  const { initialBounds, fitBoundsOptions, onMapLoad } =
    useMapFitToFeatureCollection(mapRef, mapData);

  const {
    level,
    setLevel,
    selectedFcpId,
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

  const handleReviewSaved = async () => {
    await onProjectRefresh();
    setMapPhotosRefreshKey((k) => k + 1);
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
            selectedFcpId={selectedFcpId}
          />
        </MapView>

        {(embedded || level === 'project') && (
          <MapOverlayPanels
            projectName={project.name}
            fcpCount={fcpPolygons.features.length}
            photos={mapPhotos}
          />
        )}

        {photosLoading && (
          <div className="pointer-events-none absolute left-1/2 top-3 z-10 -translate-x-1/2 rounded-full bg-white/90 px-3 py-1 text-xs text-slate-600 shadow">
            Loading photo markers…
          </div>
        )}
      </div>

      {!embedded && (
        <MapDetailColumn open={detailOpen}>
          {level === 'fcp' && selectedFcpId && (
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
                  goToPhoto(highlightedPhotoIdResolved, selectedFcpId);
                }
              }}
              onStartWarningReview={() => startWarningReview(selectedFcpId)}
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
