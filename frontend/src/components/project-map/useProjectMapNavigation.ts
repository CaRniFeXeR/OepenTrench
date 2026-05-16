import { useCallback, useEffect, useMemo, useState, type RefObject } from 'react';
import type { MapRef } from 'react-map-gl/maplibre';
import type { Feature, FeatureCollection } from 'geojson';
import type { MapLayerMouseEvent } from 'maplibre-gl';

import type { MapPhotoMarkerRead, ProjectAssetRead } from '../../api/client';
import { fitMapToFeatureCollection } from '../map/geoBounds';
import { LAYER_FCP_FILL, LAYER_PHOTOS } from './ProjectMapLayers';
import {
  buildPhotoMarkerCollection,
  photosForFcp,
  type MapLevel,
} from './mapPhotoUtils';
import { enrichFcpPolygons, splitProjectGeojson } from './splitProjectGeojson';
import { fcpCodeFromProperties, fcpLabelFromProperties } from './fcpFromProperties';

export function useProjectMapNavigation({
  mapRef,
  mapData,
  mapPhotos,
  imageAssets,
}: {
  mapRef: RefObject<MapRef | null>;
  mapData: FeatureCollection;
  mapPhotos: MapPhotoMarkerRead[];
  imageAssets: ProjectAssetRead[];
}) {
  const [level, setLevel] = useState<MapLevel>('project');
  const [selectedFcpId, setSelectedFcpId] = useState<string | null>(null);
  const [highlightedPhotoId, setHighlightedPhotoId] = useState<string | null>(null);

  const { fcpPolygons, trenches } = useMemo(() => {
    const split = splitProjectGeojson(mapData);
    return {
      fcpPolygons: enrichFcpPolygons(split.fcpPolygons),
      trenches: split.trenches,
    };
  }, [mapData]);

  const assetsById = useMemo(() => {
    const map = new Map<string, ProjectAssetRead>();
    for (const asset of imageAssets) {
      map.set(asset.id, asset);
    }
    return map;
  }, [imageAssets]);

  const navigablePhotos = useMemo(() => {
    if (selectedFcpId) return photosForFcp(mapPhotos, selectedFcpId);
    if (level === 'photo') return mapPhotos;
    return [];
  }, [mapPhotos, selectedFcpId, level]);

  const selectedFcpFeature = useMemo((): Feature | null => {
    if (!selectedFcpId) return null;
    return (
      fcpPolygons.features.find((f) => {
        const props = (f.properties ?? {}) as Record<string, unknown>;
        return String(props.fcp_id ?? '') === selectedFcpId;
      }) ?? null
    );
  }, [fcpPolygons, selectedFcpId]);

  const fcpLabel = selectedFcpFeature
    ? fcpLabelFromProperties(
        (selectedFcpFeature.properties ?? {}) as Record<string, unknown>,
      )
    : '';
  const fcpCode = selectedFcpFeature
    ? fcpCodeFromProperties(
        (selectedFcpFeature.properties ?? {}) as Record<string, unknown>,
      )
    : '';

  const highlightedPhotoIdResolved =
    highlightedPhotoId ??
    (navigablePhotos.length > 0 ? navigablePhotos[0].asset_id : null);

  const photoMarkers = useMemo(
    () =>
      buildPhotoMarkerCollection(mapPhotos, {
        highlightedPhotoId: highlightedPhotoIdResolved,
        level,
        selectedFcpId,
      }),
    [mapPhotos, highlightedPhotoIdResolved, level, selectedFcpId],
  );

  const fitToCollection = useCallback((fc: FeatureCollection) => {
    const map = mapRef.current?.getMap();
    if (!map) return;
    fitMapToFeatureCollection(map, fc);
  }, [mapRef]);

  const fitToFcp = useCallback(
    (fcpId: string) => {
      const feature = fcpPolygons.features.find((f) => {
        const props = (f.properties ?? {}) as Record<string, unknown>;
        return String(props.fcp_id ?? '') === fcpId;
      });
      if (!feature) return;
      fitToCollection({ type: 'FeatureCollection', features: [feature] });
    },
    [fcpPolygons, fitToCollection],
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
    setLevel('project');
    setSelectedFcpId(null);
    setHighlightedPhotoId(null);
    fitToCollection(mapData);
  }, [mapData, fitToCollection]);

  const goToFcp = useCallback(
    (fcpId: string) => {
      setLevel('fcp');
      setSelectedFcpId(fcpId);
      const inFcp = photosForFcp(mapPhotos, fcpId);
      setHighlightedPhotoId(inFcp[0]?.asset_id ?? null);
      fitToFcp(fcpId);
    },
    [mapPhotos, fitToFcp],
  );

  const goToPhoto = useCallback(
    (assetId: string, fcpId: string | null) => {
      setLevel('photo');
      if (fcpId) setSelectedFcpId(fcpId);
      setHighlightedPhotoId(assetId);
      easeToPhoto(assetId);
    },
    [easeToPhoto],
  );

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
    [goToFcp, goToPhoto, goToProject, level, selectedFcpId, highlightedPhotoId, mapRef],
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
    [navigablePhotos, highlightedPhotoIdResolved, level, easeToPhoto],
  );

  const activeAsset =
    highlightedPhotoIdResolved != null
      ? assetsById.get(highlightedPhotoIdResolved)
      : undefined;

  const photoIndex = highlightedPhotoIdResolved
    ? navigablePhotos.findIndex((p) => p.asset_id === highlightedPhotoIdResolved)
    : -1;

  const detailOpen = level === 'fcp' || level === 'photo';

  return {
    level,
    setLevel,
    selectedFcpId,
    fcpPolygons,
    trenches,
    photoMarkers,
    navigablePhotos,
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
  };
}
