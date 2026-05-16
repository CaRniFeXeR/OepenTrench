import type { PhotoAnalysisRead } from '../../api/client';
import { READONLY_ANALYSIS_TAGS } from '../photo-review/photoReviewCriteria';
import { PHOTO_DOC_CATEGORY_LABELS } from './photoDocumentationCategories';
import { analysisEffectiveCategory } from './photoDocumentationUtils';

export function qualityBadge(
  analysis: PhotoAnalysisRead | null | undefined,
  options?: { pendingWhenNull?: boolean },
): { label: string; className: string } {
  if (!analysis) {
    if (options?.pendingWhenNull) {
      return { label: 'Pending', className: 'bg-slate-100 text-slate-600' };
    }
    return { label: 'Failed', className: 'bg-red-100 text-red-800' };
  }

  const cat = analysisEffectiveCategory(analysis);
  if (cat === 'green') {
    return {
      label: PHOTO_DOC_CATEGORY_LABELS.green,
      className: 'bg-emerald-100 text-emerald-800',
    };
  }
  if (cat === 'yellow') {
    return {
      label: analysis.reviewed_at ? 'Warning' : 'Warning · review',
      className: 'bg-orange-100 text-orange-900',
    };
  }
  return {
    label: PHOTO_DOC_CATEGORY_LABELS.red,
    className: 'bg-red-100 text-red-800',
  };
}

export function AnalysisTag({
  label,
  ok,
  overridden,
}: {
  label: string;
  ok: boolean;
  overridden?: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs ${
        ok
          ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
          : 'border-red-200 bg-red-50 text-red-800'
      } ${overridden ? 'ring-1 ring-violet-300' : ''}`}
      title={overridden ? 'Reviewer override' : undefined}
    >
      {ok ? '✓' : '✗'} {label}
      {overridden ? ' *' : ''}
    </span>
  );
}

export function AnalysisTagRow({
  analysis,
  compact = false,
}: {
  analysis: PhotoAnalysisRead;
  compact?: boolean;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {READONLY_ANALYSIS_TAGS.map((tag) => (
        <AnalysisTag
          key={tag.key}
          label={compact ? tag.short : tag.full}
          ok={tag.ok(analysis)}
          overridden={tag.overridden(analysis)}
        />
      ))}
    </div>
  );
}
