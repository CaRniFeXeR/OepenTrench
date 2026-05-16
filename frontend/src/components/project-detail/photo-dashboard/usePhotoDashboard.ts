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
  categoryCountsFromAssetsForFcp,
  filterAssetsForDashboard,
  type TriStateFilter,
} from '../../project-images/photoDocumentationUtils';
import {
  assetIdToFcpId,
  buildFcpPhotoRows,
  buildUnassociatedPhotoRow,
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
  const [ductVisible, setDuctVisible] = useState<TriStateFilter>('all');
  const [rulerVisible, setRulerVisible] = useState<TriStateFilter>('all');
  const [privacyClear, setPrivacyClear] = useState<TriStateFilter>('all');

  const images = useMemo(() => imageAssets(project.assets), [project.assets]);
  const assetFcpMap = useMemo(() => assetIdToFcpId(mapPhotos), [mapPhotos]);
  const counts = useMemo(() => {
    if (selectedFcpId != null) {
      return categoryCountsFromAssetsForFcp(project.assets, selectedFcpId, assetFcpMap);
    }
    return categoryCountsFromAssets(project.assets);
  }, [project.assets, selectedFcpId, assetFcpMap]);
  const fcpRows = useMemo(
    () => buildFcpPhotoRows({ assets: project.assets, mapPhotos, mapData }),
    [project.assets, mapPhotos, mapData],
  );
  const unassociatedRow = useMemo(
    () => buildUnassociatedPhotoRow(project.assets, assetFcpMap),
    [project.assets, assetFcpMap],
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
        ductVisible,
        rulerVisible,
        privacyClear,
      }),
    [
      images,
      selectedCategory,
      unreviewedOnly,
      selectedFcpId,
      assetFcpMap,
      ductVisible,
      rulerVisible,
      privacyClear,
    ],
  );

  return {
    selectedCategory,
    setSelectedCategory,
    unreviewedOnly,
    setUnreviewedOnly,
    ductVisible,
    setDuctVisible,
    rulerVisible,
    setRulerVisible,
    privacyClear,
    setPrivacyClear,
    counts,
    fcpRows,
    unassociatedRow,
    selectedFcpCode,
    filteredAssets,
  };
}
