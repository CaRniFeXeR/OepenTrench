import type { Feature, FeatureCollection } from 'geojson';

import type { MapPhotoMarkerRead, PhotoDocumentationCategory } from '../../api/client';
import { isUnassociatedFcpId } from '../project-detail/fcpPhotoTableUtils';

export type MapLevel = 'project' | 'fcp' | 'photo';

export function effectiveCategory(
  category: PhotoDocumentationCategory | null | undefined,
): PhotoDocumentationCategory | 'unknown' {
  return category ?? 'unknown';
}

export function photosForFcp(
  photos: MapPhotoMarkerRead[],
  fcpId: string,
): MapPhotoMarkerRead[] {
  if (isUnassociatedFcpId(fcpId)) {
    return photos.filter((p) => p.fcp_id == null);
  }
  return photos.filter((p) => p.fcp_id === fcpId);
}

export function visiblePhotos(
  photos: MapPhotoMarkerRead[],
  level: MapLevel,
  selectedFcpId: string | null,
): MapPhotoMarkerRead[] {
  if (level === 'project') return photos;
  if (!selectedFcpId) return [];
  if (isUnassociatedFcpId(selectedFcpId)) {
    return photos.filter((p) => p.fcp_id == null);
  }
  return photosForFcp(photos, selectedFcpId);
}

export function buildPhotoMarkerCollection(
  photos: MapPhotoMarkerRead[],
  options: {
    highlightedPhotoId: string | null;
    level: MapLevel;
    selectedFcpId: string | null;
  },
): FeatureCollection {
  const { highlightedPhotoId, level, selectedFcpId } = options;
  const visible = visiblePhotos(photos, level, selectedFcpId);

  const features: Feature[] = visible.map((photo) => {
    const dimmed =
      level === 'photo' &&
      highlightedPhotoId != null &&
      photo.asset_id !== highlightedPhotoId;

    return {
      type: 'Feature',
      properties: {
        asset_id: photo.asset_id,
        category: effectiveCategory(photo.category),
        fcp_id: photo.fcp_id,
        highlighted: photo.asset_id === highlightedPhotoId,
        dimmed,
      },
      geometry: {
        type: 'Point',
        coordinates: photo.coordinates,
      },
    };
  });

  return { type: 'FeatureCollection', features };
}

export function categoryCounts(photos: MapPhotoMarkerRead[]): {
  green: number;
  yellow: number;
  red: number;
  unknown: number;
} {
  const counts = { green: 0, yellow: 0, red: 0, unknown: 0 };
  for (const photo of photos) {
    const cat = effectiveCategory(photo.category);
    if (cat === 'green') counts.green += 1;
    else if (cat === 'yellow') counts.yellow += 1;
    else if (cat === 'red') counts.red += 1;
    else counts.unknown += 1;
  }
  return counts;
}
