import type { ProjectRead } from '../api/client';

type ProjectCardProps = {
  project: ProjectRead;
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <article className="flex min-h-[160px] cursor-pointer flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300 hover:shadow-md">
      <h2 className="text-lg font-semibold text-slate-900">{project.name}</h2>
      <p className="mt-2 text-sm text-slate-500">Created {formatDate(project.created_at)}</p>
      <p className="mt-auto pt-4 font-mono text-xs text-slate-400" title={project.id}>
        {project.id.slice(0, 12)}…
      </p>
    </article>
  );
}
