import type { PhotoDocumentationCategory } from '../../../api/client';
import { PHOTO_DOC_CATEGORIES } from '../../project-images/photoDocumentationCategories';
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
  return (
    <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
      {PHOTO_DOC_CATEGORIES.map((banner) => {
        const count = counts[banner.countKey];
        const selected = selectedCategory === banner.id;
        return (
          <button
            key={banner.id}
            type="button"
            onClick={() => onSelectCategory(banner.id)}
            className={`rounded-xl border border-slate-200 p-4 text-left transition ${banner.banner.bgClass} ${
              selected
                ? `ring-2 ring-offset-2 ${banner.banner.ringClass}`
                : 'ring-0'
            }`}
          >
            <span
              className="inline-block h-3 w-3 rounded-full"
              style={{ backgroundColor: banner.color }}
              aria-hidden
            />
            <p className={`mt-2 text-sm font-semibold ${banner.banner.textClass}`}>
              {banner.label}
            </p>
            <p className={`mt-1 text-2xl font-bold tabular-nums ${banner.banner.textClass}`}>
              {count}
            </p>
            <p className="mt-0.5 text-xs text-slate-600">
              {count === 1 ? 'photo' : 'photos'}
            </p>
            {banner.id === 'yellow' && counts.warningNeedsReview > 0 && (
              <p className="mt-1 text-xs font-medium text-orange-800">
                {warningApprovalLabel(counts.warningNeedsReview, counts.yellow)}
              </p>
            )}
          </button>
        );
      })}
    </div>
  );
}
