import type { ProjectStatus } from '../api/client';

export function formatProjectDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function statusLabel(status: ProjectStatus): string {
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

export function statusChipClass(status: ProjectStatus): string {
  switch (status) {
    case 'draft':
      return 'bg-slate-100 text-slate-600 ring-slate-200';
    case 'analysing':
      return 'animate-pulse bg-sky-100 text-sky-800 ring-sky-200';
    case 'complete':
      return 'bg-emerald-100 text-emerald-800 ring-emerald-200';
    default:
      return 'bg-slate-100 text-slate-600 ring-slate-200';
  }
}

export function photoCountLabel(count: number): string {
  return `${count} Photo${count === 1 ? '' : 's'}`;
}
