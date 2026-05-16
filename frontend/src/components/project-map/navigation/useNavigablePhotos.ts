import { useMemo } from 'react';

import type { MapPhotoMarkerRead, ProjectAssetRead } from '../../../api/client';
import { photoNeedsReview } from '../../project-images/photoDocumentationUtils';
import { buildPhotoMarkerCollection, photosForFcp, type MapLevel } from '../mapPhotoUtils';

export function useNavigablePhotos({
  mapPhotos,
  imageAssets,
  selectedFcpId,
  level,
  reviewQueueMode,
  highlightedPhotoId,
}: {
  mapPhotos: MapPhotoMarkerRead[];
  imageAssets: ProjectAssetRead[];
  selectedFcpId: string | null;
  level: MapLevel;
  reviewQueueMode: boolean;
  highlightedPhotoId: string | null;
}) {
  const assetsById = useMemo(() => {
    const map = new Map<string, ProjectAssetRead>();
    for (const asset of imageAssets) {
      map.set(asset.id, asset);
    }
    return map;
  }, [imageAssets]);

  const navigablePhotos = useMemo(() => {
    let photos: MapPhotoMarkerRead[];
    if (selectedFcpId) {
      photos = photosForFcp(mapPhotos, selectedFcpId);
    } else if (level === 'photo') {
      photos = mapPhotos;
    } else {
      return [];
    }
    if (!reviewQueueMode) {
      return photos;
    }
    return photos.filter((p) => {
      const asset = assetsById.get(p.asset_id);
      return photoNeedsReview(asset?.analysis);
    });
  }, [mapPhotos, selectedFcpId, level, reviewQueueMode, assetsById]);

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

  const fcpPhotos = useMemo(() => {
    if (!selectedFcpId) return [];
    return photosForFcp(mapPhotos, selectedFcpId);
  }, [mapPhotos, selectedFcpId]);

  const warningReviewCount = useMemo(() => {
    return fcpPhotos.filter((p) =>
      photoNeedsReview(assetsById.get(p.asset_id)?.analysis),
    ).length;
  }, [fcpPhotos, assetsById]);

  const activeAsset =
    highlightedPhotoIdResolved != null
      ? assetsById.get(highlightedPhotoIdResolved)
      : undefined;

  const photoIndex = highlightedPhotoIdResolved
    ? navigablePhotos.findIndex((p) => p.asset_id === highlightedPhotoIdResolved)
    : -1;

  return {
    assetsById,
    navigablePhotos,
    highlightedPhotoIdResolved,
    photoMarkers,
    fcpPhotos,
    warningReviewCount,
    activeAsset,
    photoIndex,
  };
}
