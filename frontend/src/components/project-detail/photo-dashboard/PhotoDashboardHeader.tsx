import type { PhotoDocumentationCategory } from '../../../api/client';
import type {
  PhotoDocumentationCounts,
  TriStateFilter,
} from '../../project-images/photoDocumentationUtils';
import { CategoryBannerGrid } from './CategoryBannerGrid';

const selectClassName =
  'rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 shadow-sm focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500';

function CriteriaFilterSelect({
  label,
  value,
  onChange,
}: {
  label: string;
  value: TriStateFilter;
  onChange: (value: TriStateFilter) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-700">
      <span className="whitespace-nowrap">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as TriStateFilter)}
        className={selectClassName}
      >
        <option value="all">Any</option>
        <option value="yes">Yes</option>
        <option value="no">No</option>
      </select>
    </label>
  );
}

export function PhotoDashboardHeader({
  counts,
  selectedCategory,
  onSelectCategory,
  unreviewedOnly,
  onUnreviewedOnlyChange,
  ductVisible,
  onDuctVisibleChange,
  rulerVisible,
  onRulerVisibleChange,
  privacyClear,
  onPrivacyClearChange,
}: {
  counts: PhotoDocumentationCounts;
  selectedCategory: PhotoDocumentationCategory;
  onSelectCategory: (category: PhotoDocumentationCategory) => void;
  unreviewedOnly: boolean;
  onUnreviewedOnlyChange: (value: boolean) => void;
  ductVisible: TriStateFilter;
  onDuctVisibleChange: (value: TriStateFilter) => void;
  rulerVisible: TriStateFilter;
  onRulerVisibleChange: (value: TriStateFilter) => void;
  privacyClear: TriStateFilter;
  onPrivacyClearChange: (value: TriStateFilter) => void;
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

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
        <CriteriaFilterSelect
          label="Duct visible"
          value={ductVisible}
          onChange={onDuctVisibleChange}
        />
        <CriteriaFilterSelect
          label="Ruler visible"
          value={rulerVisible}
          onChange={onRulerVisibleChange}
        />
        <CriteriaFilterSelect
          label="Privacy"
          value={privacyClear}
          onChange={onPrivacyClearChange}
        />
      </div>
    </div>
  );
}
