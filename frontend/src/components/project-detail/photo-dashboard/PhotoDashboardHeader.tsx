import type { PhotoDocumentationCategory } from '../../../api/client';
import { aiChip, PHOTO_REVIEW_CRITERIA } from '../../photo-review/photoReviewCriteria';
import {
  cycleTriStateFilter,
  type PhotoDocumentationCounts,
  type TriStateFilter,
} from '../../project-images/photoDocumentationUtils';
import { CategoryBannerGrid } from './CategoryBannerGrid';

const DASHBOARD_FILTER_KEYS = ['duct', 'ruler', 'privacy'] as const;

function filterStateLabel(value: TriStateFilter): string {
  if (value === 'all') return 'any';
  if (value === 'yes') return 'yes';
  return 'no';
}

function CriteriaFilterBadge({
  emoji,
  name,
  label,
  value,
  onChange,
}: {
  emoji: string;
  name: string;
  label: string;
  value: TriStateFilter;
  onChange: (value: TriStateFilter) => void;
}) {
  const chip = value === 'yes' ? aiChip(true) : value === 'no' ? aiChip(false) : null;
  const stateLabel = filterStateLabel(value);

  return (
    <button
      type="button"
      onClick={() => onChange(cycleTriStateFilter(value))}
      aria-pressed={value !== 'all'}
      aria-label={`${label}: ${stateLabel}. Click to cycle filter.`}
      title={`${label}: ${stateLabel}. Click to cycle.`}
      className={`inline-flex items-center gap-1.5 rounded-lg border px-2 py-1.5 text-sm transition-colors ${
        value === 'all'
          ? 'border-transparent bg-transparent hover:bg-slate-50'
          : ''
      }`}
    >
      <span className="text-lg" aria-hidden>
        {emoji}
      </span>
      <span className="font-medium text-slate-700">{name}</span>
      {chip && (
        <span
          className={`rounded-md border px-1.5 py-0.5 text-xs font-medium ${chip.className}`}
        >
          {chip.label}
        </span>
      )}
    </button>
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
  const filterValues: Record<(typeof DASHBOARD_FILTER_KEYS)[number], TriStateFilter> = {
    duct: ductVisible,
    ruler: rulerVisible,
    privacy: privacyClear,
  };

  const filterOnChange: Record<
    (typeof DASHBOARD_FILTER_KEYS)[number],
    (value: TriStateFilter) => void
  > = {
    duct: onDuctVisibleChange,
    ruler: onRulerVisibleChange,
    privacy: onPrivacyClearChange,
  };

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

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {DASHBOARD_FILTER_KEYS.map((key) => {
          const criterion = PHOTO_REVIEW_CRITERIA.find((c) => c.key === key);
          if (!criterion) return null;
          return (
            <CriteriaFilterBadge
              key={key}
              emoji={criterion.emoji}
              name={criterion.shortLabel}
              label={criterion.label}
              value={filterValues[key]}
              onChange={filterOnChange[key]}
            />
          );
        })}
      </div>
    </div>
  );
}
