import { useMemo, useState } from 'react';

import type { PhotoDocumentationCategory, ProjectDetailRead } from '../../api/client';
import { imageAssets } from '../project-images/projectImageListUtils';
import {
  categoryCountsFromAssets,
  filterAssetsForDashboard,
} from '../project-images/photoDocumentationUtils';
import { CATEGORY_COLORS } from '../project-map/photoMarkerPaint';
import { PhotoReviewCard } from './PhotoReviewCard';

const CATEGORY_BANNERS: {
  id: PhotoDocumentationCategory;
  label: string;
  countKey: 'green' | 'yellow' | 'red';
  ringClass: string;
  bgClass: string;
  textClass: string;
}[] = [
  {
    id: 'green',
    label: 'Good',
    countKey: 'green',
    ringClass: 'ring-emerald-500',
    bgClass: 'bg-emerald-50 hover:bg-emerald-100/80',
    textClass: 'text-emerald-900',
  },
  {
    id: 'yellow',
    label: 'Warning',
    countKey: 'yellow',
    ringClass: 'ring-orange-500',
    bgClass: 'bg-orange-50 hover:bg-orange-100/80',
    textClass: 'text-orange-900',
  },
  {
    id: 'red',
    label: 'Failed',
    countKey: 'red',
    ringClass: 'ring-red-500',
    bgClass: 'bg-red-50 hover:bg-red-100/80',
    textClass: 'text-red-900',
  },
];

function warningApprovalLabel(needsReview: number, yellowTotal: number): string {
  const noun = needsReview === 1 ? 'needs' : 'need';
  if (needsReview < yellowTotal) {
    return `${needsReview} of ${yellowTotal} ${noun} approval`;
  }
  return `${needsReview} ${noun} approval`;
}

function emptyMessage(
  category: PhotoDocumentationCategory,
  unreviewedOnly: boolean,
): string {
  const label =
    category === 'green' ? 'good' : category === 'yellow' ? 'warning' : 'failed';
  if (unreviewedOnly) {
    return `No unreviewed ${label} photos.`;
  }
  return `No ${label} photos.`;
}

export function ProjectPhotoDashboard({
  project,
  onRefresh,
}: {
  project: ProjectDetailRead;
  onRefresh: () => Promise<void>;
}) {
  const [selectedCategory, setSelectedCategory] =
    useState<PhotoDocumentationCategory>('yellow');
  const [unreviewedOnly, setUnreviewedOnly] = useState(false);

  const images = useMemo(() => imageAssets(project.assets), [project.assets]);
  const counts = useMemo(() => categoryCountsFromAssets(project.assets), [project.assets]);

  const filteredAssets = useMemo(
    () =>
      filterAssetsForDashboard(images, {
        category: selectedCategory,
        unreviewedOnly,
      }),
    [images, selectedCategory, unreviewedOnly],
  );

  const handleReviewSaved = async () => {
    await onRefresh();
  };

  return (
    <section className="flex min-h-0 flex-1 flex-col overflow-hidden bg-slate-50">
      <div className="border-b border-slate-200 bg-white px-4 py-4 sm:px-6">
        <h2 className="text-lg font-semibold text-slate-900">Photo documentation</h2>
        <p className="mt-1 text-sm text-slate-600">
          Review and approve photos by documentation category.
        </p>

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          {CATEGORY_BANNERS.map((banner) => {
            const count = counts[banner.countKey];
            const selected = selectedCategory === banner.id;
            return (
              <button
                key={banner.id}
                type="button"
                onClick={() => setSelectedCategory(banner.id)}
                className={`rounded-xl border border-slate-200 p-4 text-left transition ${banner.bgClass} ${
                  selected
                    ? `ring-2 ring-offset-2 ${banner.ringClass}`
                    : 'ring-0'
                }`}
              >
                <span
                  className="inline-block h-3 w-3 rounded-full"
                  style={{ backgroundColor: CATEGORY_COLORS[banner.id] }}
                  aria-hidden
                />
                <p className={`mt-2 text-sm font-semibold ${banner.textClass}`}>
                  {banner.label}
                </p>
                <p className={`mt-1 text-2xl font-bold tabular-nums ${banner.textClass}`}>
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

        {counts.pending > 0 && (
          <p className="mt-3 text-xs text-slate-500">
            {counts.pending} photo{counts.pending === 1 ? '' : 's'} pending analysis.
          </p>
        )}

        <label className="mt-4 flex cursor-pointer items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={unreviewedOnly}
            onChange={(e) => setUnreviewedOnly(e.target.checked)}
            className="h-4 w-4 rounded border-slate-300 text-violet-700 focus:ring-violet-500"
          />
          Unreviewed only
          {selectedCategory === 'yellow' && unreviewedOnly && (
            <span className="text-xs text-orange-800">(warning review queue)</span>
          )}
        </label>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-6">
        {filteredAssets.length === 0 ? (
          <p className="py-12 text-center text-sm text-slate-500">
            {emptyMessage(selectedCategory, unreviewedOnly)}
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
