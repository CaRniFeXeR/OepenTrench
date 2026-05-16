import type { PhotoAnalysisRead } from '../../api/client';
import { effectiveCategory } from '../project-map/mapPhotoUtils';

export function qualityBadge(
  analysis: PhotoAnalysisRead | null | undefined,
  options?: { pendingWhenNull?: boolean },
): { label: string; className: string } {
  if (!analysis) {
    if (options?.pendingWhenNull) {
      return { label: 'Pending', className: 'bg-slate-100 text-slate-600' };
    }
    return { label: 'Missing', className: 'bg-red-100 text-red-800' };
  }

  const cat = effectiveCategory(
    analysis.reviewer_override_category ?? analysis.category ?? null,
  );
  if (cat === 'green') {
    return { label: 'Good', className: 'bg-emerald-100 text-emerald-800' };
  }
  if (cat === 'yellow') {
    return { label: 'Poor', className: 'bg-amber-100 text-amber-900' };
  }
  return { label: 'Missing', className: 'bg-red-100 text-red-800' };
}

export function AnalysisTag({
  label,
  ok,
}: {
  label: string;
  ok: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs ${
        ok
          ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
          : 'border-red-200 bg-red-50 text-red-800'
      }`}
    >
      {ok ? '✓' : '✗'} {label}
    </span>
  );
}

const ANALYSIS_TAGS = [
  { key: 'duct', full: 'Duct visible', short: 'Duct', ok: (a: PhotoAnalysisRead) => a.has_duct },
  { key: 'sand', full: 'Sand bedding', short: 'Sand', ok: (a: PhotoAnalysisRead) => a.has_sand_bedding },
  { key: 'ruler', full: 'Burial depth / ruler', short: 'Ruler', ok: (a: PhotoAnalysisRead) => a.has_ruler },
  { key: 'seal', full: 'Pipe end seal', short: 'Seal', ok: (a: PhotoAnalysisRead) => a.has_pipe_end_seal },
  { key: 'gps', full: 'GPS match', short: 'GPS', ok: (a: PhotoAnalysisRead) => a.gps_matches_route },
  { key: 'date', full: 'Date valid', short: 'Date', ok: (a: PhotoAnalysisRead) => a.date_valid },
  {
    key: 'privacy',
    full: 'Privacy clear',
    short: 'Privacy',
    ok: (a: PhotoAnalysisRead) => !a.has_gdpr_problems,
  },
] as const;

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
        />
      ))}
    </div>
  );
}
