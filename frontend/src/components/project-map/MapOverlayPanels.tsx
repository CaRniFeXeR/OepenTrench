import type { MapPhotoMarkerRead } from '../../api/client';
import { categoryCounts } from './mapPhotoUtils';
import { CATEGORY_COLORS } from './photoMarkerPaint';

export function MapOverlayPanels({
  projectName,
  fcpCount,
  photos,
}: {
  projectName: string;
  fcpCount: number;
  photos: MapPhotoMarkerRead[];
}) {
  const counts = categoryCounts(photos);
  const total = photos.length;
  const greenPct = total ? Math.round((counts.green / total) * 100) : 0;
  const yellowPct = total ? Math.round((counts.yellow / total) * 100) : 0;
  const redPct = total ? Math.round((counts.red / total) * 100) : 0;

  return (
    <>
      <div className="pointer-events-none absolute left-3 top-3 z-10 max-w-xs rounded-lg border border-slate-200 bg-white/95 p-3 text-xs shadow-md backdrop-blur-sm">
        <p className="font-semibold text-slate-900">Network structure</p>
        <ul className="mt-2 space-y-1 text-slate-600">
          <li className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-sm bg-violet-600" />
            FCP — fiber concentration area
          </li>
          <li className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-slate-500" />
            Trench route segment
          </li>
          <li className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500" />
            Documented photo (GPS)
          </li>
        </ul>
        <p className="mt-2 text-slate-500">
          Identifies trench sections where documentation may not meet requirements.
        </p>
      </div>

      <div className="pointer-events-none absolute bottom-3 left-3 right-3 z-10 flex flex-wrap items-end justify-between gap-3">
        <div className="rounded-lg border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-md backdrop-blur-sm">
          <p className="font-medium text-slate-900">
            {projectName} · {fcpCount} FCPs · {photos.length} GPS photos
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white/95 px-3 py-2 shadow-md backdrop-blur-sm">
          <p className="mb-1 text-xs font-medium text-slate-700">Photo documentation</p>
          <DocumentationBar greenPct={greenPct} yellowPct={yellowPct} redPct={redPct} />
        </div>
      </div>

      <div className="pointer-events-none absolute right-3 top-3 z-10 w-40 rounded-lg border border-slate-200 bg-white/95 p-3 text-xs shadow-md backdrop-blur-sm">
        <p className="mb-2 font-semibold text-slate-900">Photo status</p>
        <StatusRow label="Complete" pct={greenPct} color={CATEGORY_COLORS.green} />
        <StatusRow label="Partial" pct={yellowPct} color={CATEGORY_COLORS.yellow} />
        <StatusRow label="Missing" pct={redPct} color={CATEGORY_COLORS.red} />
      </div>
    </>
  );
}

function DocumentationBar({
  greenPct,
  yellowPct,
  redPct,
}: {
  greenPct: number;
  yellowPct: number;
  redPct: number;
}) {
  return (
    <div className="flex h-2 w-48 overflow-hidden rounded-full">
      {greenPct > 0 && (
        <div
          className="h-full"
          style={{ width: `${greenPct}%`, backgroundColor: CATEGORY_COLORS.green }}
        />
      )}
      {yellowPct > 0 && (
        <div
          className="h-full"
          style={{ width: `${yellowPct}%`, backgroundColor: CATEGORY_COLORS.yellow }}
        />
      )}
      {redPct > 0 && (
        <div
          className="h-full"
          style={{ width: `${redPct}%`, backgroundColor: CATEGORY_COLORS.red }}
        />
      )}
    </div>
  );
}

function StatusRow({
  label,
  pct,
  color,
}: {
  label: string;
  pct: number;
  color: string;
}) {
  return (
    <div className="mb-1.5 flex items-center justify-between gap-2">
      <span className="flex items-center gap-1.5 text-slate-600">
        <span
          className="inline-block h-2 w-2 rounded-sm"
          style={{ backgroundColor: color }}
        />
        {label}
      </span>
      <span className="font-medium text-slate-800">{pct}%</span>
    </div>
  );
}
