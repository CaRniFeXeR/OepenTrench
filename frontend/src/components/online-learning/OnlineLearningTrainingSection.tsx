import type { OnlineLearningStatsRead } from '../../api/client';

import { useOnlineLearningTrainings } from './useOnlineLearningTrainings';

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  if (m === 0) return `${s}s`;
  return `${m}m ${s}s`;
}

function formatStarted(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function statusLabel(status: string): string {
  switch (status) {
    case 'running':
      return 'Running';
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    case 'pending':
      return 'Pending';
    default:
      return status;
  }
}

export function OnlineLearningTrainingSection({
  stats,
}: {
  stats: OnlineLearningStatsRead | null;
}) {
  const { trainings, loading, error, startError, isTraining, startTraining } =
    useOnlineLearningTrainings();

  const canStart = !isTraining && (stats?.total_mismatch ?? 0) > 0;

  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-4 sm:px-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Model training</h2>
            <p className="mt-1 text-sm text-slate-600">
              Retrain on reviewed photos where reviewers corrected the AI.
            </p>
          </div>
          <button
            type="button"
            disabled={!canStart}
            onClick={() => void startTraining()}
            className="shrink-0 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-45"
          >
            {isTraining ? 'Training…' : 'Start new training'}
          </button>
        </div>
        {startError ? (
          <p className="mt-3 text-sm text-red-600">{startError}</p>
        ) : null}
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[480px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50 text-xs font-medium uppercase tracking-wide text-slate-500">
              <th className="px-4 py-3 sm:px-6" scope="col">
                Started
              </th>
              <th className="px-4 py-3" scope="col">
                Photos
              </th>
              <th className="px-4 py-3" scope="col">
                Duration
              </th>
              <th className="px-4 py-3 sm:pr-6" scope="col">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && trainings.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-500 sm:px-6">
                  Loading training runs…
                </td>
              </tr>
            ) : null}
            {!loading && trainings.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-500 sm:px-6">
                  No training runs yet.
                </td>
              </tr>
            ) : null}
            {trainings.map((run) => (
              <tr key={run.id} className="hover:bg-slate-50/80">
                <td className="whitespace-nowrap px-4 py-3 sm:px-6 text-slate-700">
                  {formatStarted(run.started_at)}
                </td>
                <td className="px-4 py-3 text-slate-700">{run.photo_count}</td>
                <td className="px-4 py-3 text-slate-700">
                  {run.status === 'running'
                    ? '…'
                    : run.duration_sec != null
                      ? formatDuration(run.duration_sec)
                      : '—'}
                </td>
                <td className="px-4 py-3 sm:pr-6">
                  <span
                    className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      run.status === 'completed'
                        ? 'bg-emerald-100 text-emerald-800'
                        : run.status === 'running' || run.status === 'pending'
                          ? 'bg-amber-100 text-amber-900'
                          : 'bg-red-100 text-red-800'
                    }`}
                    title={run.error_message ?? undefined}
                  >
                    {statusLabel(run.status)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
