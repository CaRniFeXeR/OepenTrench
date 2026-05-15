import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  readProjectProjectsProjectIdGet,
  type ProjectDetailRead,
} from '../api/client';

function statusLabel(status: ProjectDetailRead['status']): string {
  switch (status) {
    case 'draft':
      return 'Draft';
    case 'analysing':
      return 'Analysing';
    case 'complete':
      return 'Complete';
    default:
      return status;
  }
}

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectDetailRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!projectId) {
      setError('Missing project id.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    const { data, error: apiError } = await readProjectProjectsProjectIdGet({
      path: { project_id: projectId },
    });
    setLoading(false);

    if (apiError) {
      setError('Project not found or failed to load.');
      setProject(null);
      return;
    }

    setProject(data ?? null);
  }, [projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-4">
          <Link
            to="/"
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            ← Back to projects
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        {loading && <p className="text-slate-500">Loading project…</p>}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
        {!loading && !error && project && (
          <>
            <div className="mb-6">
              <h1 className="text-2xl font-semibold text-slate-900">{project.name}</h1>
              <p className="mt-1 text-sm text-slate-500">
                {project.region ?? 'Region not set'} · {statusLabel(project.status)}
              </p>
            </div>
            <section className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">
              Upload panel (photos & GeoJSON) will live here.
            </section>
          </>
        )}
      </main>
    </div>
  );
}
