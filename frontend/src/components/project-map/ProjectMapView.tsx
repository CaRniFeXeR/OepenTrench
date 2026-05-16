import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { MapRef } from 'react-map-gl/maplibre';
import type { Feature, FeatureCollection } from 'geojson';
import type { MapLayerMouseEvent } from 'maplibre-gl';

import type { ProjectDetailRead, ProjectAssetRead } from '../../api/client';
import { MapView } from '../map/MapView';
import { fitMapToFeatureCollection } from '../map/geoBounds';
import { useMapFitToFeatureCollection } from '../map/useMapFitToFeatureCollection';
import { FcpSummaryPanel } from './FcpSummaryPanel';
import { MapOverlayPanels } from './MapOverlayPanels';
import { MapSidePanel, type SidePanelMode } from './MapSidePanel';
import {
  LAYER_FCP_FILL,
  LAYER_PHOTOS,
  ProjectMapLayers,
} from './ProjectMapLayers';
import { TrenchImageDetailPanel } from './TrenchImageDetailPanel';
import {
  buildPhotoMarkerCollection,
  photosForFcp,
  type MapLevel,
} from './mapPhotoUtils';
import { enrichFcpPolygons, splitProjectGeojson } from './splitProjectGeojson';
import { fcpCodeFromProperties, fcpLabelFromProperties } from './fcpFromProperties';
import { useProjectMapData } from './useProjectMapData';

export function ProjectMapView({
  project,
  mapData,
  height = 560,
}: {
  project: ProjectDetailRead;
  mapData: FeatureCollection;
  height?: number;
}) {
  const mapRef = useRef<MapRef | null>(null);
  const [level, setLevel] = useState<MapLevel>('project');
  const [selectedFcpId, setSelectedFcpId] = useState<string | null>(null);
  const [highlightedPhotoId, setHighlightedPhotoId] = useState<string | null>(null);

  const imageCount = project.assets.filter((a) => a.kind === 'image').length;
  const { mapPhotos, loading: photosLoading } = useProjectMapData(
    project.id,
    imageCount,
  );

  const { fcpPolygons, trenches } = useMemo(() => {
    const split = splitProjectGeojson(mapData);
    return {
      fcpPolygons: enrichFcpPolygons(split.fcpPolygons),
      trenches: split.trenches,
    };
  }, [mapData]);

  const { initialBounds, fitBoundsOptions, onMapLoad } =
    useMapFitToFeatureCollection(mapRef, mapData);

  const assetsById = useMemo(() => {
    const map = new Map<string, ProjectAssetRead>();
    for (const asset of project.assets) {
      if (asset.kind === 'image') map.set(asset.id, asset);
    }
    return map;
  }, [project.assets]);

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
  }, []);

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
    [mapPhotos],
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
    [goToFcp, goToPhoto, goToProject, level, selectedFcpId, highlightedPhotoId],
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

  const sidePanelMode: SidePanelMode =
    level === 'fcp' ? 'fcp' : level === 'photo' ? 'photo' : 'hidden';

  const activeAsset =
    highlightedPhotoIdResolved != null
      ? assetsById.get(highlightedPhotoIdResolved)
      : undefined;

  const photoIndex = highlightedPhotoIdResolved
    ? navigablePhotos.findIndex((p) => p.asset_id === highlightedPhotoIdResolved)
    : -1;

  return (
    <div
      className="relative overflow-hidden rounded-xl border border-slate-200 bg-slate-100 shadow-sm"
      style={{ height }}
    >
      <MapView
        ref={mapRef}
        className="h-full w-full"
        height={height}
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

      {level === 'project' && (
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

      <MapSidePanel mode={sidePanelMode}>
        {level === 'fcp' && selectedFcpId && (
          <FcpSummaryPanel
            fcpLabel={fcpLabel}
            fcpCode={fcpCode}
            projectName={project.name}
            photos={navigablePhotos}
            highlightedPhotoId={highlightedPhotoIdResolved}
            onBack={goToProject}
            onPrevPhoto={() => stepPhoto(-1)}
            onNextPhoto={() => stepPhoto(1)}
            onOpenPhoto={() => {
              if (highlightedPhotoIdResolved) {
                goToPhoto(highlightedPhotoIdResolved, selectedFcpId);
              }
            }}
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
              onBack={() => {
                setLevel('fcp');
              }}
              onPrev={() => stepPhoto(-1)}
              onNext={() => stepPhoto(1)}
            />
          )}
      </MapSidePanel>
    </div>
  );
}
