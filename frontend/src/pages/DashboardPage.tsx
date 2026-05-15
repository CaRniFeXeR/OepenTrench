import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  listProjectsRouteProjectsGet,
  type ProjectRead,
  type ProjectStatus,
} from '../api/client';
import { CreateProjectCard } from '../components/CreateProjectCard';
import { ProjectCard } from '../components/ProjectCard';

type StatusFilter = ProjectStatus | 'all';

type SortOption = 'name_asc' | 'name_desc' | 'newest';

function sortProjects(projects: ProjectRead[], sort: SortOption): ProjectRead[] {
  const copy = [...projects];
  if (sort === 'name_asc') {
    copy.sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base' }));
  } else if (sort === 'name_desc') {
    copy.sort((a, b) => b.name.localeCompare(a.name, undefined, { sensitivity: 'base' }));
  } else {
    copy.sort((a, b) => {
      const ta = new Date(a.updated_at ?? a.created_at).getTime();
      const tb = new Date(b.updated_at ?? b.created_at).getTime();
      return tb - ta;
    });
  }
  return copy;
}

function filterProjects(
  projects: ProjectRead[],
  statusFilter: StatusFilter,
  query: string,
): ProjectRead[] {
  const q = query.trim().toLowerCase();
  return projects.filter((p) => {
    if (statusFilter !== 'all' && p.status !== statusFilter) {
      return false;
    }
    if (!q) {
      return true;
    }
    const name = p.name.toLowerCase();
    const region = (p.region ?? '').toLowerCase();
    return name.includes(q) || region.includes(q);
  });
}

export function DashboardPage() {
  const [projects, setProjects] = useState<ProjectRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [searchText, setSearchText] = useState('');
  const [sort, setSort] = useState<SortOption>('newest');

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

  const visibleProjects = useMemo(
    () => sortProjects(filterProjects(projects, statusFilter, searchText), sort),
    [projects, statusFilter, searchText, sort],
  );

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <span className="text-lg font-semibold tracking-tight text-slate-900">öGIG</span>
          <div className="flex flex-1 justify-center px-4">
            <input
              type="search"
              name="global-search"
              placeholder="Search…"
              disabled
              aria-disabled="true"
              title="Global search — coming later"
              className="w-full max-w-md rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500"
            />
          </div>
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-medium text-slate-600"
            title="Profile"
          >
            U
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <h1 className="text-2xl font-semibold text-slate-900">Trench Quality Projects</h1>
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <span className="whitespace-nowrap">Filter</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
              >
                <option value="all">All statuses</option>
                <option value="draft">Draft</option>
                <option value="analysing">Analysing</option>
                <option value="complete">Complete</option>
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <span className="whitespace-nowrap">Project / region</span>
              <input
                type="search"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                placeholder="Filter by name or region"
                className="min-w-[12rem] rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
              />
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <span className="whitespace-nowrap">Sort</span>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value as SortOption)}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
              >
                <option value="newest">Newest activity</option>
                <option value="name_asc">Name A–Z</option>
                <option value="name_desc">Name Z–A</option>
              </select>
            </label>
          </div>
        </div>

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

        {!loading && !error && projects.length > 0 && visibleProjects.length === 0 && (
          <p className="mb-6 text-center text-slate-500">No projects match your filters.</p>
        )}

        {!loading && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <CreateProjectCard onCreated={loadProjects} />
            {visibleProjects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
