import type { PhotoDocumentationCategory } from '../../../api/client';
import { FcpPhotoTable } from '../FcpPhotoTable';
import type { FcpPhotoRow } from '../fcpPhotoTableUtils';
import { CategoryBannerGrid } from './CategoryBannerGrid';

export function PhotoDashboardHeader({
  counts,
  fcpRows,
  selectedFcpId,
  onSelectFcp,
  selectedCategory,
  onSelectCategory,
  unreviewedOnly,
  onUnreviewedOnlyChange,
}: {
  counts: {
    green: number;
    yellow: number;
    red: number;
    pending: number;
    warningNeedsReview: number;
  };
  fcpRows: FcpPhotoRow[];
  selectedFcpId: string | null;
  onSelectFcp: (fcpId: string | null) => void;
  selectedCategory: PhotoDocumentationCategory;
  onSelectCategory: (category: PhotoDocumentationCategory) => void;
  unreviewedOnly: boolean;
  onUnreviewedOnlyChange: (value: boolean) => void;
}) {
  return (
    <div className="border-b border-slate-200 bg-white px-4 py-4 sm:px-6">
      <h2 className="text-lg font-semibold text-slate-900">Photo documentation</h2>
      <p className="mt-1 text-sm text-slate-600">
        Review and approve photos by documentation category.
      </p>

      <CategoryBannerGrid
        counts={counts}
        selectedCategory={selectedCategory}
        onSelectCategory={onSelectCategory}
      />

      <FcpPhotoTable
        rows={fcpRows}
        selectedFcpId={selectedFcpId}
        onSelectFcp={onSelectFcp}
      />

      {counts.pending > 0 && (
        <p className="mt-3 text-xs text-slate-500">
          {counts.pending} photo{counts.pending === 1 ? '' : 's'} pending analysis.
        </p>
      )}

      <label className="mt-4 flex cursor-pointer items-center gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={unreviewedOnly}
          onChange={(e) => onUnreviewedOnlyChange(e.target.checked)}
          className="h-4 w-4 rounded border-slate-300 text-violet-700 focus:ring-violet-500"
        />
        Unreviewed only
        {selectedCategory === 'yellow' && unreviewedOnly && (
          <span className="text-xs text-orange-800">(warning review queue)</span>
        )}
      </label>
    </div>
  );
}
