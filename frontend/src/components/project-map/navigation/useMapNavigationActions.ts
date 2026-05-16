import { useCallback, useEffect, useRef, type RefObject } from 'react';
import type { MapRef } from 'react-map-gl/maplibre';
import type { Feature, FeatureCollection } from 'geojson';
import type { MapLayerMouseEvent } from 'maplibre-gl';

import type { MapPhotoMarkerRead, ProjectAssetRead } from '../../../api/client';
import { photoNeedsReview } from '../../project-images/photoDocumentationUtils';
import { fitMapToFeatureCollection } from '../../map/geoBounds';
import { LAYER_FCP_FILL, LAYER_PHOTOS } from '../ProjectMapLayers';
import { photosForFcp, type MapLevel } from '../mapPhotoUtils';

export function useMapNavigationActions({
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
}: {
  mapRef: RefObject<MapRef | null>;
  mapData: FeatureCollection;
  mapPhotos: MapPhotoMarkerRead[];
  assetsById: Map<string, ProjectAssetRead>;
  fitToFcpFeature: (fcpId: string) => Feature | undefined;
  navigablePhotos: MapPhotoMarkerRead[];
  highlightedPhotoIdResolved: string | null;
  selectedFcpId: string | null;
  level: MapLevel;
  setLevel: (level: MapLevel) => void;
  highlightedPhotoId: string | null;
  setHighlightedPhotoId: (id: string | null) => void;
  setReviewQueueMode: (mode: boolean) => void;
  updateSelectedFcpId: (id: string | null) => void;
  isControlled: boolean;
  controlledSelectedFcpId?: string | null;
}) {
  const skipExternalSyncRef = useRef(false);

  const fitToCollection = useCallback(
    (fc: FeatureCollection) => {
      const map = mapRef.current?.getMap();
      if (!map) return;
      fitMapToFeatureCollection(map, fc);
    },
    [mapRef],
  );

  const fitToFcp = useCallback(
    (fcpId: string) => {
      const feature = fitToFcpFeature(fcpId);
      if (!feature) return;
      fitToCollection({ type: 'FeatureCollection', features: [feature] });
    },
    [fitToFcpFeature, fitToCollection],
  );

  const easeToPhoto = useCallback(
    (assetId: string) => {
      const photo = mapPhotos.find((p) => p.asset_id === assetId);
      const map = mapRef.current?.getMap();
      if (!photo || !map) return;
      map.easeTo({
        center: photo.coordinates,
        zoom: 17,
        duration: 600,
      });
    },
    [mapPhotos, mapRef],
  );

  const goToProject = useCallback(() => {
    skipExternalSyncRef.current = true;
    setLevel('project');
    updateSelectedFcpId(null);
    setHighlightedPhotoId(null);
    setReviewQueueMode(false);
    fitToCollection(mapData);
  }, [mapData, fitToCollection, updateSelectedFcpId, setLevel, setHighlightedPhotoId, setReviewQueueMode]);

  const goToFcp = useCallback(
    (fcpId: string) => {
      skipExternalSyncRef.current = true;
      setLevel('fcp');
      updateSelectedFcpId(fcpId);
      const inFcp = photosForFcp(mapPhotos, fcpId);
      setHighlightedPhotoId(inFcp[0]?.asset_id ?? null);
      fitToFcp(fcpId);
    },
    [mapPhotos, fitToFcp, updateSelectedFcpId, setLevel, setHighlightedPhotoId],
  );

  const goToPhoto = useCallback(
    (assetId: string, fcpId: string | null) => {
      skipExternalSyncRef.current = true;
      setLevel('photo');
      if (fcpId) updateSelectedFcpId(fcpId);
      setHighlightedPhotoId(assetId);
      easeToPhoto(assetId);
    },
    [easeToPhoto, updateSelectedFcpId, setLevel, setHighlightedPhotoId],
  );

  useEffect(() => {
    if (!isControlled) return;
    if (skipExternalSyncRef.current) {
      skipExternalSyncRef.current = false;
      return;
    }

    const fcpId = controlledSelectedFcpId ?? null;
    if (fcpId == null) {
      setLevel('project');
      setHighlightedPhotoId(null);
      setReviewQueueMode(false);
      fitToCollection(mapData);
      return;
    }

    setLevel('fcp');
    const inFcp = photosForFcp(mapPhotos, fcpId);
    setHighlightedPhotoId(inFcp[0]?.asset_id ?? null);
    fitToFcp(fcpId);
  }, [
    isControlled,
    controlledSelectedFcpId,
    mapPhotos,
    mapData,
    fitToFcp,
    fitToCollection,
    setLevel,
    setHighlightedPhotoId,
    setReviewQueueMode,
  ]);

  useEffect(() => {
    if (level === 'fcp' && selectedFcpId) {
      fitToFcp(selectedFcpId);
    }
  }, [level, selectedFcpId, fitToFcp]);

  useEffect(() => {
    if (level === 'photo' && highlightedPhotoId) {
      easeToPhoto(highlightedPhotoId);
    }
  }, [level, highlightedPhotoId, easeToPhoto]);

  const handleMapClick = useCallback(
    (event: MapLayerMouseEvent) => {
      const map = mapRef.current?.getMap();
      if (!map) return;

      const photoHits = map.queryRenderedFeatures(event.point, {
        layers: [LAYER_PHOTOS],
      });
      if (photoHits.length > 0) {
        const assetId = String(photoHits[0].properties?.asset_id ?? '');
        const fcpId = photoHits[0].properties?.fcp_id;
        if (assetId) {
          goToPhoto(assetId, fcpId != null ? String(fcpId) : selectedFcpId);
          return;
        }
      }

      const fcpHits = map.queryRenderedFeatures(event.point, {
        layers: [LAYER_FCP_FILL],
      });
      if (fcpHits.length > 0) {
        const fcpId = String(fcpHits[0].properties?.fcp_id ?? '');
        if (fcpId) {
          if (level === 'project') {
            goToFcp(fcpId);
          } else if (level === 'photo' && fcpId === selectedFcpId) {
            setLevel('fcp');
            setHighlightedPhotoId(highlightedPhotoId);
          } else if (fcpId !== selectedFcpId) {
            goToFcp(fcpId);
          }
          return;
        }
      }

      if (level !== 'project') {
        goToProject();
      }
    },
    [
      goToFcp,
      goToPhoto,
      goToProject,
      level,
      selectedFcpId,
      highlightedPhotoId,
      mapRef,
      setLevel,
      setHighlightedPhotoId,
    ],
  );

  const stepPhoto = useCallback(
    (delta: number) => {
      if (navigablePhotos.length === 0) return;
      const currentId = highlightedPhotoIdResolved ?? navigablePhotos[0].asset_id;
      const idx = navigablePhotos.findIndex((p) => p.asset_id === currentId);
      const nextIdx =
        idx < 0
          ? 0
          : (idx + delta + navigablePhotos.length) % navigablePhotos.length;
      const nextId = navigablePhotos[nextIdx].asset_id;
      setHighlightedPhotoId(nextId);
      if (level === 'photo') {
        easeToPhoto(nextId);
      }
    },
    [navigablePhotos, highlightedPhotoIdResolved, level, easeToPhoto, setHighlightedPhotoId],
  );

  const startWarningReview = useCallback(
    (fcpId: string) => {
      skipExternalSyncRef.current = true;
      const inFcp = photosForFcp(mapPhotos, fcpId);
      const first = inFcp.find((p) => photoNeedsReview(assetsById.get(p.asset_id)?.analysis));
      setReviewQueueMode(true);
      setLevel('photo');
      updateSelectedFcpId(fcpId);
      if (first) {
        setHighlightedPhotoId(first.asset_id);
        easeToPhoto(first.asset_id);
      } else {
        setHighlightedPhotoId(inFcp[0]?.asset_id ?? null);
        if (fcpId) fitToFcp(fcpId);
      }
    },
    [
      mapPhotos,
      assetsById,
      easeToPhoto,
      fitToFcp,
      updateSelectedFcpId,
      setReviewQueueMode,
      setLevel,
      setHighlightedPhotoId,
    ],
  );

  return {
    goToProject,
    goToFcp,
    goToPhoto,
    handleMapClick,
    stepPhoto,
    startWarningReview,
  };
}
