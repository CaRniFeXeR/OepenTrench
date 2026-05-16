import type { PhotoDocumentationCategory } from '../../../api/client';
import { PHOTO_DOC_CATEGORIES } from '../../project-images/photoDocumentationCategories';
import { categoryPercentages } from '../../ui/DocumentationStatusBar';
import { warningApprovalLabel } from './photoDashboardMessages';

export function CategoryBannerGrid({
  counts,
  selectedCategory,
  onSelectCategory,
}: {
  counts: {
    green: number;
    yellow: number;
    red: number;
    warningNeedsReview: number;
  };
  selectedCategory: PhotoDocumentationCategory;
  onSelectCategory: (category: PhotoDocumentationCategory) => void;
}) {
  const { greenPct, yellowPct, redPct } = categoryPercentages(counts);
  const pctByKey = { green: greenPct, yellow: yellowPct, red: redPct } as const;

  return (
    <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
      {PHOTO_DOC_CATEGORIES.map((banner) => {
        const count = counts[banner.countKey];
        const pct = pctByKey[banner.countKey];
        const selected = selectedCategory === banner.id;
        return (
          <button
            key={banner.id}
            type="button"
            onClick={() => onSelectCategory(banner.id)}
            className={`flex items-start justify-between gap-3 rounded-xl border border-slate-200 px-3 py-2.5 text-left transition ${banner.banner.bgClass} ${
              selected
                ? `ring-2 ring-offset-1 ${banner.banner.ringClass}`
                : 'ring-0'
            }`}
          >
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: banner.color }}
                  aria-hidden
                />
                <span className={`text-sm font-semibold ${banner.banner.textClass}`}>
                  {banner.label}
                </span>
              </div>
              {banner.id === 'yellow' && counts.warningNeedsReview > 0 && (
                <p className="mt-1 text-xs font-medium text-orange-800">
                  {warningApprovalLabel(counts.warningNeedsReview, counts.yellow)}
                </p>
              )}
            </div>
            <div className="shrink-0 text-right tabular-nums">
              <p className={`text-xl font-bold leading-none ${banner.banner.textClass}`}>
                {count}
              </p>
              <p className="mt-0.5 text-xs text-slate-600">
                {pct}% · {count === 1 ? 'photo' : 'photos'}
              </p>
            </div>
          </button>
        );
      })}
    </div>
  );
}
