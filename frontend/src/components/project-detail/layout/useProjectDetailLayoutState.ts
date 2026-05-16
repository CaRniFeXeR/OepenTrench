import { useCallback, useState } from 'react';

export type DetailWorkspaceTab = 'files' | 'analysis';

export function useProjectDetailLayoutState(onRefresh: () => Promise<void>) {
  const [activeTab, setActiveTab] = useState<DetailWorkspaceTab>('files');
  const [selectedFcpId, setSelectedFcpId] = useState<string | null>(null);
  const [mapPhotosRefreshKey, setMapPhotosRefreshKey] = useState(0);

  const handleRefresh = useCallback(async () => {
    await onRefresh();
    setMapPhotosRefreshKey((k) => k + 1);
  }, [onRefresh]);

  return {
    activeTab,
    setActiveTab,
    selectedFcpId,
    setSelectedFcpId,
    mapPhotosRefreshKey,
    handleRefresh,
  };
}
