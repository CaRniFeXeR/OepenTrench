import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  readProjectProjectsProjectIdGet,
  type ProjectDetailRead,
} from '../api/client';
import { ProjectUploadPanel } from '../components/project-upload/ProjectUploadPanel';

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectDetailRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadsBusy, setUploadsBusy] = useState(false);

  const load = useCallback(async (options?: { silent?: boolean }) => {
    if (!projectId) {
      setError('Missing project id.');
      setLoading(false);
      return;
    }

    const silent = options?.silent ?? false;
    if (!silent) {
      setLoading(true);
    }
    setError(null);
    const { data, error: apiError } = await readProjectProjectsProjectIdGet({
      path: { project_id: projectId },
    });
    if (!silent) {
      setLoading(false);
    }

    if (apiError) {
      setError('Project not found or failed to load.');
      setProject(null);
      return;
    }

    setProject(data ?? null);
  }, [projectId]);

  const refreshProject = useCallback(async () => {
    await load({ silent: true });
  }, [load]);

  useEffect(() => {
    queueMicrotask(() => {
      void load();
    });
  }, [load]);

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-4">
          <Link
            to="/"
            aria-disabled={uploadsBusy}
            onClick={(e) => {
              if (uploadsBusy) e.preventDefault();
            }}
            className={`text-sm font-medium text-slate-600 hover:text-slate-900 ${
              uploadsBusy ? 'pointer-events-none opacity-50' : ''
            }`}
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
          <ProjectUploadPanel
            project={project}
            onRefresh={refreshProject}
            onUploadsBusyChange={setUploadsBusy}
          />
        )}
      </main>
    </div>
  );
}

