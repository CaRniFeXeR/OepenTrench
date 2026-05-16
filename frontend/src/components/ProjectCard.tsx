import { useNavigate } from 'react-router-dom';

import type { ProjectRead } from '../api/client';
import {
  formatProjectDate,
  photoCountLabel,
  statusChipClass,
  statusLabel,
} from '../helpers/projectFormatters';

type ProjectCardProps = {
  project: ProjectRead;
};

export function ProjectCard({ project }: ProjectCardProps) {
  const navigate = useNavigate();
  const photos = project.photo_count ?? 0;
  const hasUpdated = Boolean(project.updated_at);
  const dateIso = hasUpdated ? project.updated_at! : project.created_at;
  const datePrefix = hasUpdated ? 'Updated' : 'Created';

  function handleClick() {
    navigate(`/projects/${project.id}`);
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className="flex min-h-[160px] w-full cursor-pointer flex-col rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:border-slate-300 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-400"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-900">{project.name}</h2>
        <span
          className={`inline-flex shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${statusChipClass(project.status)}`}
        >
          {statusLabel(project.status)}
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        {project.region?.trim() ? project.region : 'Region not set'}
      </p>
      <p className="mt-2 text-sm text-slate-500">
        {datePrefix} {formatProjectDate(dateIso)}
      </p>
      <p className="mt-auto pt-4 text-sm font-medium text-slate-700">{photoCountLabel(photos)}</p>
    </button>
  );
}
