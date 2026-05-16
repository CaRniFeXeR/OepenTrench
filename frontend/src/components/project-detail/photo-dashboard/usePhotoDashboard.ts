import { useMemo, useState } from 'react';
import type { FeatureCollection } from 'geojson';

import type {
  MapPhotoMarkerRead,
  PhotoDocumentationCategory,
  ProjectDetailRead,
} from '../../../api/client';
import { imageAssets } from '../../project-images/projectImageListUtils';
import {
  categoryCountsFromAssets,
  filterAssetsForDashboard,
} from '../../project-images/photoDocumentationUtils';
import {
  assetIdToFcpId,
  buildFcpPhotoRows,
  fcpCodeForId,
} from '../fcpPhotoTableUtils';

export function usePhotoDashboard({
  project,
  mapData,
  mapPhotos,
  selectedFcpId,
}: {
  project: ProjectDetailRead;
  mapData: FeatureCollection | null;
  mapPhotos: MapPhotoMarkerRead[];
  selectedFcpId: string | null;
}) {
  const [selectedCategory, setSelectedCategory] =
    useState<PhotoDocumentationCategory>('yellow');
  const [unreviewedOnly, setUnreviewedOnly] = useState(false);

  const images = useMemo(() => imageAssets(project.assets), [project.assets]);
  const counts = useMemo(() => categoryCountsFromAssets(project.assets), [project.assets]);
  const assetFcpMap = useMemo(() => assetIdToFcpId(mapPhotos), [mapPhotos]);
  const fcpRows = useMemo(
    () => buildFcpPhotoRows({ assets: project.assets, mapPhotos, mapData }),
    [project.assets, mapPhotos, mapData],
  );
  const selectedFcpCode = useMemo(
    () => fcpCodeForId(fcpRows, selectedFcpId),
    [fcpRows, selectedFcpId],
  );

  const filteredAssets = useMemo(
    () =>
      filterAssetsForDashboard(images, {
        category: selectedCategory,
        unreviewedOnly,
        fcpId: selectedFcpId,
        assetFcpMap,
      }),
    [images, selectedCategory, unreviewedOnly, selectedFcpId, assetFcpMap],
  );

  return {
    selectedCategory,
    setSelectedCategory,
    unreviewedOnly,
    setUnreviewedOnly,
    counts,
    fcpRows,
    selectedFcpCode,
    filteredAssets,
  };
}
