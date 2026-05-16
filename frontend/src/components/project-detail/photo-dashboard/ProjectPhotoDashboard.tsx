import type { FeatureCollection } from 'geojson';

import type { MapPhotoMarkerRead, ProjectDetailRead } from '../../../api/client';
import { FcpSidePanel } from '../FcpSidePanel';
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
  } = usePhotoDashboard({ project, mapData, mapPhotos, selectedFcpId });

  const handleReviewSaved = async () => {
    await onRefresh();
  };

  return (
    <section className="flex min-h-0 flex-1 overflow-hidden bg-slate-50">
      <FcpSidePanel
        projectName={project.name}
        rows={fcpRows}
        unassociatedRow={unassociatedRow}
        selectedFcpId={selectedFcpId}
        onSelectFcp={onSelectedFcpIdChange}
        onClearFcpFilter={() => onSelectedFcpIdChange(null)}
      />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <PhotoDashboardHeader
          counts={counts}
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
          unreviewedOnly={unreviewedOnly}
          onUnreviewedOnlyChange={setUnreviewedOnly}
          ductVisible={ductVisible}
          onDuctVisibleChange={setDuctVisible}
          rulerVisible={rulerVisible}
          onRulerVisibleChange={setRulerVisible}
          privacyClear={privacyClear}
          onPrivacyClearChange={setPrivacyClear}
        />

        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-6">
          {filteredAssets.length === 0 ? (
            <p className="py-12 text-center text-sm text-slate-500">
              {emptyMessage(selectedCategory, unreviewedOnly, selectedFcpCode, {
                ductVisible,
                rulerVisible,
                privacyClear,
              })}
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
      </div>
    </section>
  );
}
