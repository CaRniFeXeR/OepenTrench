import { useEffect, useMemo, useState } from 'react';
import type { FeatureCollection } from 'geojson';

import type { MapPhotoMarkerRead, ProjectDetailRead } from '../../../api/client';
import { FcpSidePanel } from '../FcpSidePanel';
import { PhotoReviewCard } from '../PhotoReviewCard';
import { emptyMessage } from './photoDashboardMessages';
import { paginatePage } from './paginatePage';
import { PhotoDashboardHeader } from './PhotoDashboardHeader';
import { usePhotoDashboard } from './usePhotoDashboard';

const PAGE_SIZE = 12;

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
  const [page, setPage] = useState(1);

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

  const { pageItems, totalPages, startIndex, endIndex } = useMemo(
    () => paginatePage(filteredAssets, page, PAGE_SIZE),
    [filteredAssets, page],
  );

  useEffect(() => {
    setPage(1);
  }, [
    selectedCategory,
    unreviewedOnly,
    selectedFcpId,
    ductVisible,
    rulerVisible,
    privacyClear,
  ]);

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
            <>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {pageItems.map((asset) => (
                  <PhotoReviewCard
                    key={asset.id}
                    projectId={project.id}
                    asset={asset}
                    onSaved={handleReviewSaved}
                    showDuplicateControl={selectedCategory === 'red'}
                  />
                ))}
              </div>

              <footer className="mt-6 flex flex-col gap-3 border-t border-slate-200 pt-4 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-slate-600">
                  Showing {startIndex + 1}–{endIndex} of {filteredAssets.length}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-slate-600">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
                  >
                    Next
                  </button>
                </div>
              </footer>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
