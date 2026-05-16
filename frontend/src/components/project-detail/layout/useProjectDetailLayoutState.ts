import { useCallback, useState } from 'react';

export function useProjectDetailLayoutState(onRefresh: () => Promise<void>) {
  const [uploadDrawerOpen, setUploadDrawerOpen] = useState(true);
  const [selectedFcpId, setSelectedFcpId] = useState<string | null>(null);
  const [mapPhotosRefreshKey, setMapPhotosRefreshKey] = useState(0);

  const handleRefresh = useCallback(async () => {
    await onRefresh();
    setMapPhotosRefreshKey((k) => k + 1);
  }, [onRefresh]);

  return {
    uploadDrawerOpen,
    setUploadDrawerOpen,
    selectedFcpId,
    setSelectedFcpId,
    mapPhotosRefreshKey,
    handleRefresh,
  };
}
