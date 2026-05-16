import type { FcpCoverageRead } from '../../../api/client';
import type { FcpPhotoRow } from '../fcpPhotoTableUtils';
import { formatCoveragePct } from './reportStatsUtils';

function fcpDisplayLabel(fcpCode: string, fcpLabel: string): string {
  if (fcpCode && fcpCode !== fcpLabel) return `${fcpCode} — ${fcpLabel}`;
  return fcpCode || fcpLabel;
}

export function ReportCoverageTable({
  fcpRows,
  unassociatedRow,
  coverage,
  coverageLoading,
}: {
  fcpRows: FcpPhotoRow[];
  unassociatedRow: FcpPhotoRow | null;
  coverage: FcpCoverageRead | null;
  coverageLoading: boolean;
}) {
  const hasCoverage = coverage?.project.computed_at != null;
  const summaries = [...(coverage?.summaries ?? [])].sort((a, b) => {
    const codeA = a.fcp_code ?? a.fcp_label ?? a.fcp_id;
    const codeB = b.fcp_code ?? b.fcp_label ?? b.fcp_id;
    return codeA.localeCompare(codeB, undefined, { sensitivity: 'base' });
  });

  const rowByFcpId = new Map(fcpRows.map((r) => [r.fcpId, r]));

  let totalGreen = 0;
  let totalYellow = 0;
  let totalRed = 0;
  for (const row of fcpRows) {
    totalGreen += row.green;
    totalYellow += row.yellow;
    totalRed += row.red;
  }
  if (unassociatedRow) {
    totalGreen += unassociatedRow.green;
    totalYellow += unassociatedRow.yellow;
    totalRed += unassociatedRow.red;
  }

  if (fcpRows.length === 0 && !unassociatedRow) {
    return null;
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm print:shadow-none print:break-inside-avoid">
      <header className="border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-900">Coverage & documentation by FCP</h3>
        <p className="mt-0.5 text-xs text-slate-500">
          Trench segment coverage and photo category counts per FCP.
        </p>
      </header>

      <div className="px-4 py-3">
        {coverageLoading && !coverage && (
          <p className="print:hidden text-xs text-slate-500">Loading coverage…</p>
        )}

        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full min-w-[28rem] text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 print:table-header-group">
              <tr>
                <th className="px-3 py-2 font-medium">FCP</th>
                <th className="px-3 py-2 font-medium text-right">Coverage</th>
                <th className="px-3 py-2 font-medium text-right">Good</th>
                <th className="px-3 py-2 font-medium text-right">Warning</th>
                <th className="px-3 py-2 font-medium text-right">Failed</th>
              </tr>
            </thead>
            <tbody>
              {summaries.map((summary) => {
                const photoRow = rowByFcpId.get(summary.fcp_id);
                return (
                  <tr key={summary.fcp_id} className="border-t border-slate-100 bg-white">
                    <td className="max-w-[12rem] truncate px-3 py-2 font-medium text-slate-900">
                      {fcpDisplayLabel(
                        summary.fcp_code ?? summary.fcp_id,
                        summary.fcp_label ?? summary.fcp_id,
                      )}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-slate-800">
                      {hasCoverage ? formatCoveragePct(summary.coverage_ratio) : '—'}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-emerald-800">
                      {photoRow?.green ?? 0}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-orange-800">
                      {photoRow?.yellow ?? 0}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-red-800">
                      {photoRow?.red ?? 0}
                    </td>
                  </tr>
                );
              })}
              {unassociatedRow && (
                <tr className="border-t border-slate-100 bg-white">
                  <td className="px-3 py-2 font-medium text-slate-900">
                    {unassociatedRow.fcpCode}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums text-slate-500">—</td>
                  <td className="px-3 py-2 text-right tabular-nums text-emerald-800">
                    {unassociatedRow.green}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums text-orange-800">
                    {unassociatedRow.yellow}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums text-red-800">
                    {unassociatedRow.red}
                  </td>
                </tr>
              )}
              {fcpRows
                .filter((r) => !summaries.some((s) => s.fcp_id === r.fcpId))
                .map((row) => (
                  <tr key={row.fcpId} className="border-t border-slate-100 bg-white">
                    <td className="max-w-[12rem] truncate px-3 py-2 font-medium text-slate-900">
                      {fcpDisplayLabel(row.fcpCode, row.fcpLabel)}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-slate-500">—</td>
                    <td className="px-3 py-2 text-right tabular-nums text-emerald-800">
                      {row.green}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-orange-800">
                      {row.yellow}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-red-800">
                      {row.red}
                    </td>
                  </tr>
                ))}
            </tbody>
            <tfoot className="border-t-2 border-slate-200 bg-slate-50 font-semibold text-slate-900">
              <tr>
                <td className="px-3 py-2">Total</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {hasCoverage && coverage
                    ? formatCoveragePct(coverage.project.coverage_ratio)
                    : '—'}
                </td>
                <td className="px-3 py-2 text-right tabular-nums text-emerald-800">
                  {totalGreen}
                </td>
                <td className="px-3 py-2 text-right tabular-nums text-orange-800">
                  {totalYellow}
                </td>
                <td className="px-3 py-2 text-right tabular-nums text-red-800">{totalRed}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </section>
  );
}
