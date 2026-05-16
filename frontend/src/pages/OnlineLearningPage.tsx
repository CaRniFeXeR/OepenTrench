import { Link } from 'react-router-dom';

import { OnlineLearningMismatchTable } from '../components/online-learning/OnlineLearningMismatchTable';
import { OnlineLearningStatsBar } from '../components/online-learning/OnlineLearningStatsBar';
import { OnlineLearningTrainingSection } from '../components/online-learning/OnlineLearningTrainingSection';
import { useOnlineLearningDisagreements } from '../components/online-learning/useOnlineLearningDisagreements';

export function OnlineLearningPage() {
  const {
    items,
    stats,
    total,
    loading,
    error,
    page,
    setPage,
    pageSize,
    setPageSize,
    totalPages,
    startIndex,
    endIndex,
  } = useOnlineLearningDisagreements();

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <Link
            to="/"
            className="text-lg font-semibold tracking-tight text-slate-900 hover:text-slate-600"
          >
            öGIG
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link to="/" className="text-slate-600 hover:text-slate-900">
              Projects
            </Link>
            <span className="font-medium text-slate-900">Online learning</span>
          </nav>
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-medium text-slate-600"
            title="Profile"
          >
            U
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-8">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Online learning</h1>
          <p className="mt-1 text-sm text-slate-600">
            Cross-project photos where human reviewers corrected AI labels — used to improve the
            model.
          </p>
        </div>

        <OnlineLearningStatsBar stats={stats} loading={loading} />

        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        <OnlineLearningMismatchTable
          items={items}
          total={total}
          loading={loading}
          page={page}
          pageSize={pageSize}
          totalPages={totalPages}
          startIndex={startIndex}
          endIndex={endIndex}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
        />

        <OnlineLearningTrainingSection stats={stats} />
      </main>
    </div>
  );
}
