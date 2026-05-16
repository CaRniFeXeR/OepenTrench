import { useCallback, useState } from 'react';

import type { OnlineLearningStatsRead } from '../../api/client';

export type TrainingRun = {
  id: string;
  startedAt: Date;
  photoCount: number;
  durationSec: number;
  status: 'completed' | 'running' | 'failed';
};

const SEED_TRAININGS: TrainingRun[] = [
  {
    id: 'seed-1',
    startedAt: new Date('2026-05-10T14:22:00Z'),
    photoCount: 128,
    durationSec: 342,
    status: 'completed',
  },
  {
    id: 'seed-2',
    startedAt: new Date('2026-05-02T09:05:00Z'),
    photoCount: 94,
    durationSec: 281,
    status: 'completed',
  },
  {
    id: 'seed-3',
    startedAt: new Date('2026-04-18T16:40:00Z'),
    photoCount: 67,
    durationSec: 195,
    status: 'completed',
  },
];

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  if (m === 0) return `${s}s`;
  return `${m}m ${s}s`;
}

function formatStarted(d: Date): string {
  return d.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

export function OnlineLearningTrainingSection({
  stats,
}: {
  stats: OnlineLearningStatsRead | null;
}) {
  const [trainings, setTrainings] = useState<TrainingRun[]>(SEED_TRAININGS);
  const [isTraining, setIsTraining] = useState(false);

  const startTraining = useCallback(async () => {
    if (isTraining) return;
    const photoCount = stats?.total_mismatch ?? 0;
    const startedAt = new Date();
    const runId = `run-${Date.now()}`;

    setIsTraining(true);
    setTrainings((prev) => [
      {
        id: runId,
        startedAt,
        photoCount,
        durationSec: 0,
        status: 'running',
      },
      ...prev,
    ]);

    const durationSec = 2 + Math.floor(Math.random() * 2);
    await new Promise((resolve) => setTimeout(resolve, durationSec * 1000));

    setTrainings((prev) =>
      prev.map((t) =>
        t.id === runId
          ? { ...t, durationSec, status: 'completed' as const }
          : t,
      ),
    );
    setIsTraining(false);
  }, [isTraining, stats?.total_mismatch]);

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
            disabled={isTraining || (stats?.total_mismatch ?? 0) === 0}
            onClick={() => void startTraining()}
            className="shrink-0 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-45"
          >
            {isTraining ? 'Training…' : 'Start new training'}
          </button>
        </div>
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
            {trainings.map((run) => (
              <tr key={run.id} className="hover:bg-slate-50/80">
                <td className="whitespace-nowrap px-4 py-3 sm:px-6 text-slate-700">
                  {formatStarted(run.startedAt)}
                </td>
                <td className="px-4 py-3 text-slate-700">{run.photoCount}</td>
                <td className="px-4 py-3 text-slate-700">
                  {run.status === 'running' ? '…' : formatDuration(run.durationSec)}
                </td>
                <td className="px-4 py-3 sm:pr-6">
                  <span
                    className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      run.status === 'completed'
                        ? 'bg-emerald-100 text-emerald-800'
                        : run.status === 'running'
                          ? 'bg-amber-100 text-amber-900'
                          : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {run.status === 'running' ? 'Running' : run.status === 'completed' ? 'Completed' : 'Failed'}
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
