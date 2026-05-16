import { PHOTO_DOC_CATEGORIES } from '../../project-images/photoDocumentationCategories';
import { ReportStatValue } from './ReportStatValue';
import {
  formatCoveragePct,
  type ReportCategoryStats,
  type ReportCoverageDetail,
  type ReportPredictionStat,
} from './reportStatsUtils';

export function ReportStatsBlock({
  categoryStats,
  predictionStats,
  coverage,
}: {
  categoryStats: ReportCategoryStats;
  predictionStats: ReportPredictionStat[];
  coverage: ReportCoverageDetail;
}) {
  const pctByKey = {
    green: categoryStats.greenPct,
    yellow: categoryStats.yellowPct,
    red: categoryStats.redPct,
  } as const;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <h4 className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Documentation
          </h4>
          <ul className="mt-2 space-y-2">
            {PHOTO_DOC_CATEGORIES.map((cat) => (
              <li
                key={cat.id}
                className={`flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2 ${cat.banner.bgClass}`}
              >
                <div className="flex min-w-0 items-center gap-2">
                  <span
                    className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ backgroundColor: cat.color }}
                    aria-hidden
                  />
                  <span className={`text-sm font-medium ${cat.banner.textClass}`}>
                    {cat.label}
                  </span>
                </div>
                <ReportStatValue
                  absolute={categoryStats[cat.countKey]}
                  percentage={pctByKey[cat.countKey]}
                />
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Analysis checks
          </h4>
          <ul className="mt-2 space-y-2">
            {predictionStats.map((row) => (
              <li
                key={row.key}
                className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2"
              >
                <div className="flex min-w-0 items-center gap-2">
                  <span className="text-lg" aria-hidden>
                    {row.emoji}
                  </span>
                  <span className="text-sm font-medium text-slate-800">{row.label}</span>
                </div>
                <ReportStatValue absolute={row.pass} percentage={row.pct} />
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
        <h4 className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Coverage
        </h4>
        {coverage ? (
          <p className="mt-1 text-sm text-slate-800">
            <span className="text-lg font-semibold tabular-nums">
              {formatCoveragePct(coverage.coverageRatio)}
            </span>
            <span className="text-slate-600">
              {' '}
              · {coverage.coveredCount}/{coverage.compartmentCount} segments covered
            </span>
          </p>
        ) : (
          <p className="mt-1 text-sm text-slate-500">Not calculated</p>
        )}
      </div>

      {categoryStats.pending > 0 && (
        <p className="text-xs text-slate-500">
          {categoryStats.pending} photo{categoryStats.pending === 1 ? '' : 's'} pending analysis
          (excluded from percentages above).
        </p>
      )}
    </div>
  );
}
