import { useState, type RefObject } from 'react';
import type { MapRef } from 'react-map-gl/maplibre';
import type { FeatureCollection } from 'geojson';

import type { MapPhotoMarkerRead, ProjectAssetRead } from '../../../api/client';
import type { MapLevel } from '../mapPhotoUtils';
import { useControlledFcpSelection } from './useControlledFcpSelection';
import { useMapGeoLayers } from './useMapGeoLayers';
import { useMapNavigationActions } from './useMapNavigationActions';
import { useNavigablePhotos } from './useNavigablePhotos';

export function useProjectMapNavigation({
  mapRef,
  mapData,
  mapPhotos,
  imageAssets,
  selectedFcpId: controlledSelectedFcpId,
  onSelectedFcpIdChange,
}: {
  mapRef: RefObject<MapRef | null>;
  mapData: FeatureCollection;
  mapPhotos: MapPhotoMarkerRead[];
  imageAssets: ProjectAssetRead[];
  selectedFcpId?: string | null;
  onSelectedFcpIdChange?: (id: string | null) => void;
}) {
  const [level, setLevel] = useState<MapLevel>('project');
  const [highlightedPhotoId, setHighlightedPhotoId] = useState<string | null>(null);
  const [reviewQueueMode, setReviewQueueMode] = useState(false);

  const { isControlled, selectedFcpId, updateSelectedFcpId } = useControlledFcpSelection({
    controlledSelectedFcpId,
    onSelectedFcpIdChange,
  });

  const { fcpPolygons, trenches, fcpLabel, fcpCode, fitToFcpFeature } = useMapGeoLayers(
    mapData,
    selectedFcpId,
  );

  const {
    assetsById,
    navigablePhotos,
    highlightedPhotoIdResolved,
    photoMarkers,
    fcpPhotos,
    warningReviewCount,
    activeAsset,
    photoIndex,
  } = useNavigablePhotos({
    mapPhotos,
    imageAssets,
    selectedFcpId,
    level,
    reviewQueueMode,
    highlightedPhotoId,
  });

  const {
    goToProject,
    goToFcp,
    goToPhoto,
    handleMapClick,
    stepPhoto,
    startWarningReview,
  } = useMapNavigationActions({
    mapRef,
    mapData,
    mapPhotos,
    assetsById,
    fitToFcpFeature,
    navigablePhotos,
    highlightedPhotoIdResolved,
    selectedFcpId,
    level,
    setLevel,
    highlightedPhotoId,
    setHighlightedPhotoId,
    setReviewQueueMode,
    updateSelectedFcpId,
    isControlled,
    controlledSelectedFcpId,
  });

  const detailOpen = level === 'fcp' || level === 'photo';

  return {
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
    goToFcp,
    goToPhoto,
    handleMapClick,
    stepPhoto,
    reviewQueueMode,
    setReviewQueueMode,
    startWarningReview,
    warningReviewCount,
  };
}
