import type { OnlineLearningStatsRead } from '../../api/client';
import { emptyStats } from './useOnlineLearningDisagreements';

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
      {sub ? <p className="mt-0.5 text-sm text-slate-600">{sub}</p> : null}
    </div>
  );
}


export function OnlineLearningStatsBar({
  stats,
  loading,
}: {
  stats: OnlineLearningStatsRead | null;
  loading: boolean;
}) {
  const s = stats ?? emptyStats();
  const ratePct =
    s.total_reviewed > 0 ? `${(s.mismatch_rate * 100).toFixed(1)}%` : '—';

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        label="Reviewed photos"
        value={loading ? '…' : String(s.total_reviewed)}
        sub="All projects"
      />
      <StatCard
        label="AI vs reviewer mismatch"
        value={loading ? '…' : String(s.total_mismatch)}
        sub="Training candidates"
      />
      <StatCard label="Mismatch rate" value={loading ? '…' : ratePct} sub="Of reviewed photos" />
      <StatCard
        label="Projects with mismatch"
        value={loading ? '…' : String(s.projects_with_mismatch)}
      />
    </div>
  );
}
