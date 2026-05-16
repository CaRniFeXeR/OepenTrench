import type { PhotoAnalysisRead } from '../../api/client';
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
    return { label: 'Good', className: 'bg-emerald-100 text-emerald-800' };
  }
  if (cat === 'yellow') {
    return {
      label: analysis.reviewed_at ? 'Warning' : 'Warning · review',
      className: 'bg-orange-100 text-orange-900',
    };
  }
  return { label: 'Failed', className: 'bg-red-100 text-red-800' };
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

type AnalysisTagDef = {
  key: string;
  full: string;
  short: string;
  ok: (a: PhotoAnalysisRead) => boolean;
  overridden: (a: PhotoAnalysisRead) => boolean;
};

const ANALYSIS_TAGS: AnalysisTagDef[] = [
  {
    key: 'duct',
    full: 'Duct visible',
    short: 'Duct',
    ok: (a) => a.effective_has_duct,
    overridden: (a) => a.reviewer_has_duct != null,
  },
  {
    key: 'ruler',
    full: 'Burial depth / ruler',
    short: 'Ruler',
    ok: (a) => a.effective_has_ruler,
    overridden: (a) => a.reviewer_has_ruler != null,
  },
  {
    key: 'domain',
    full: 'In domain',
    short: 'Domain',
    ok: (a) => a.effective_is_in_domain,
    overridden: (a) => a.reviewer_is_in_domain != null,
  },
  {
    key: 'gps',
    full: 'GPS match',
    short: 'GPS',
    ok: (a) => a.effective_gps_matches_route,
    overridden: (a) => a.reviewer_gps_matches_route != null,
  },
  {
    key: 'date',
    full: 'Date valid',
    short: 'Date',
    ok: (a) => a.date_valid,
    overridden: () => false,
  },
  {
    key: 'privacy',
    full: 'Privacy clear',
    short: 'Privacy',
    ok: (a) => !a.effective_has_gdpr_problems,
    overridden: (a) => a.reviewer_has_gdpr_problems != null,
  },
];

export function AnalysisTagRow({
  analysis,
  compact = false,
}: {
  analysis: PhotoAnalysisRead;
  compact?: boolean;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {ANALYSIS_TAGS.map((tag) => (
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
