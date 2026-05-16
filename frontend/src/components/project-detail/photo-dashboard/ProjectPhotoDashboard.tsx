import type { FeatureCollection } from 'geojson';

import type { MapPhotoMarkerRead, ProjectDetailRead } from '../../../api/client';
import { PhotoReviewCard } from '../PhotoReviewCard';
import { emptyMessage } from './photoDashboardMessages';
import { PhotoDashboardHeader } from './PhotoDashboardHeader';
import { usePhotoDashboard } from './usePhotoDashboard';

export function ProjectPhotoDashboard({
  project,
  mapData,
  mapPhotos,
  selectedFcpId,
  onSelectedFcpIdChange,
  onRefresh,
}: {
  project: ProjectDetailRead;
  mapData: FeatureCollection | null;
  mapPhotos: MapPhotoMarkerRead[];
  selectedFcpId: string | null;
  onSelectedFcpIdChange: (fcpId: string | null) => void;
  onRefresh: () => Promise<void>;
}) {
  const {
    selectedCategory,
    setSelectedCategory,
    unreviewedOnly,
    setUnreviewedOnly,
    counts,
    fcpRows,
    selectedFcpCode,
    filteredAssets,
  } = usePhotoDashboard({ project, mapData, mapPhotos, selectedFcpId });

  const handleReviewSaved = async () => {
    await onRefresh();
  };

  return (
    <section className="flex min-h-0 flex-1 flex-col overflow-hidden bg-slate-50">
      <PhotoDashboardHeader
        counts={counts}
        fcpRows={fcpRows}
        selectedFcpId={selectedFcpId}
        onSelectFcp={onSelectedFcpIdChange}
        selectedCategory={selectedCategory}
        onSelectCategory={setSelectedCategory}
        unreviewedOnly={unreviewedOnly}
        onUnreviewedOnlyChange={setUnreviewedOnly}
      />

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-6">
        {filteredAssets.length === 0 ? (
          <p className="py-12 text-center text-sm text-slate-500">
            {emptyMessage(selectedCategory, unreviewedOnly, selectedFcpCode)}
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {filteredAssets.map((asset) => (
              <PhotoReviewCard
                key={asset.id}
                projectId={project.id}
                asset={asset}
                onSaved={handleReviewSaved}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
