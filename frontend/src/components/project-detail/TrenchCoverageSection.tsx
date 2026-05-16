import type { FcpCoverageRead } from '../../api/client';

function formatCoveragePct(ratio: number): string {
  return `${Math.round(ratio * 100)}%`;
}

function formatComputedAt(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function fcpDisplayLabel(fcpCode: string | null, fcpLabel: string | null): string {
  if (fcpCode) return fcpCode;
  if (fcpLabel) return fcpLabel;
  return '—';
}

export function TrenchCoverageSection({
  coverage,
  loading,
  error,
  selectedFcpId,
  showCalculateButton = false,
  calculating = false,
  routeReady = true,
  onCalculate,
  className = '',
  embedded = false,
}: {
  coverage: FcpCoverageRead | null;
  loading: boolean;
  error?: string | null;
  selectedFcpId?: string | null;
  showCalculateButton?: boolean;
  calculating?: boolean;
  routeReady?: boolean;
  onCalculate?: () => void;
  className?: string;
  embedded?: boolean;
}) {
  const project = coverage?.project;
  const hasData = project != null && project.computed_at != null;
  const summaries = [...(coverage?.summaries ?? [])].sort((a, b) => {
    const codeA = a.fcp_code ?? a.fcp_label ?? a.fcp_id;
    const codeB = b.fcp_code ?? b.fcp_label ?? b.fcp_id;
    return codeA.localeCompare(codeB, undefined, { sensitivity: 'base' });
  });

  return (
    <section
      className={`${embedded ? 'rounded-xl border border-slate-200 bg-white shadow-sm print:shadow-none' : 'shrink-0 border-t border-slate-200 bg-white'} ${className}`}
    >
      <div className="border-b border-slate-100 px-4 py-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2
              className={
                embedded
                  ? 'text-sm font-semibold text-slate-900'
                  : 'text-base font-semibold text-slate-900'
              }
            >
              Trench coverage
            </h2>
            {project?.computed_at && (
              <p className="mt-0.5 text-xs text-slate-500">
                Last calculated {formatComputedAt(project.computed_at)}
              </p>
            )}
          </div>
          {showCalculateButton && onCalculate && (
            <button
              type="button"
              onClick={() => void onCalculate()}
              disabled={!routeReady || calculating || loading}
              className="print:hidden rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {calculating ? 'Calculating…' : 'Calculate trench coverage'}
            </button>
          )}
        </div>
      </div>

      <div className="px-4 py-3">
        {error && (
          <p className="mb-2 text-xs text-red-600 print:hidden" role="alert">
            {error}
          </p>
        )}

        {loading && !coverage && (
          <p className="text-xs text-slate-500 print:hidden">Loading coverage…</p>
        )}

        {!loading && !hasData && (
          <p className="text-xs text-slate-500">Not calculated yet.</p>
        )}

        {hasData && project && (
          <div className="mb-3 flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <p className="text-2xl font-semibold text-slate-900">
              {formatCoveragePct(project.coverage_ratio)}
            </p>
            <p className="text-xs text-slate-600">
              {project.covered_count}/{project.compartment_count} segments covered ·{' '}
              {project.fcp_count} FCPs
            </p>
          </div>
        )}

        {summaries.length > 0 && (
          <div
            className={`rounded-lg border border-slate-200 ${embedded ? '' : 'max-h-64 overflow-y-auto print:max-h-none print:overflow-visible'}`}
          >
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 print:table-header-group">
                <tr>
                  <th className="px-3 py-2 font-medium">FCP</th>
                  <th className="px-3 py-2 font-medium text-right">Coverage</th>
                  <th className="px-3 py-2 font-medium text-right">Segments</th>
                </tr>
              </thead>
              <tbody>
                {summaries.map((row) => {
                  const segmentLabel =
                    row.compartment_count === 1 ? 'segment' : 'segments';
                  const selected = selectedFcpId === row.fcp_id;
                  return (
                    <tr
                      key={row.fcp_id}
                      className={`border-t border-slate-100 ${
                        selected ? 'bg-violet-50' : 'bg-white'
                      }`}
                    >
                      <td className="max-w-[12rem] truncate px-3 py-2 font-medium text-slate-900">
                        {fcpDisplayLabel(row.fcp_code, row.fcp_label)}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums text-slate-800">
                        {formatCoveragePct(row.coverage_ratio)}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums text-slate-600">
                        {row.covered_count}/{row.compartment_count} {segmentLabel}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
