import { useCallback, useEffect, useState } from 'react';

import {
  listProjectsRouteProjectsGet,
  type ProjectRead,
} from '../api/client';
import { CreateProjectCard } from '../components/CreateProjectCard';
import { ProjectCard } from '../components/ProjectCard';

export function DashboardPage() {
  const [projects, setProjects] = useState<ProjectRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = useCallback(async () => {
    setLoading(true);
    setError(null);

    const { data, error: apiError } = await listProjectsRouteProjectsGet({
      query: { limit: 50, offset: 0 },
    });

    setLoading(false);

    if (apiError) {
      setError('Failed to load projects. Is the API running on port 8000?');
      return;
    }

    setProjects(data ?? []);
  }, []);

  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <h1 className="text-2xl font-semibold text-slate-900">ÖpenTrench</h1>
          <p className="mt-1 text-sm text-slate-500">Trench documentation projects</p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        {loading && (
          <p className="text-center text-slate-500">Loading projects…</p>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {!loading && !error && projects.length === 0 && (
          <p className="mb-6 text-center text-slate-500">
            No projects yet. Create your first one below.
          </p>
        )}

        {!loading && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
            <CreateProjectCard onCreated={loadProjects} />
          </div>
        )}
      </main>
    </div>
  );
}
