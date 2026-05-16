import type { MapPhotoMarkerRead } from '../../api/client';
import { categoryCounts } from './mapPhotoUtils';
import { CATEGORY_COLORS } from './photoMarkerPaint';

export function FcpSummaryPanel({
  fcpLabel,
  fcpCode,
  projectName,
  photos,
  highlightedPhotoId,
  onBack,
  onPrevPhoto,
  onNextPhoto,
  onOpenPhoto,
}: {
  fcpLabel: string;
  fcpCode: string;
  projectName: string;
  photos: MapPhotoMarkerRead[];
  highlightedPhotoId: string | null;
  onBack: () => void;
  onPrevPhoto: () => void;
  onNextPhoto: () => void;
  onOpenPhoto: () => void;
}) {
  const counts = categoryCounts(photos);
  const total = photos.length;
  const greenPct = total ? Math.round((counts.green / total) * 100) : 0;
  const yellowPct = total ? Math.round((counts.yellow / total) * 100) : 0;
  const redPct = total ? Math.round((counts.red / total) * 100) : 0;

  const highlightIndex = highlightedPhotoId
    ? photos.findIndex((p) => p.asset_id === highlightedPhotoId)
    : -1;

  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-4">
      <button
        type="button"
        onClick={onBack}
        className="mb-3 text-left text-sm font-medium text-violet-700 hover:text-violet-900"
      >
        ← Back to project
      </button>

      <h2 className="text-lg font-semibold text-slate-900">{fcpCode}</h2>
      <p className="text-sm text-slate-600">{fcpLabel}</p>
      <p className="mt-1 text-xs text-slate-500">Cluster / project: {projectName}</p>

      <dl className="mt-4 text-sm text-slate-700">
        <dt className="text-slate-500">Photos in FCP</dt>
        <dd className="font-medium">{photos.length} documented</dd>
      </dl>

      <div className="mt-4">
        <p className="mb-1 text-xs font-medium text-slate-600">Status in this FCP</p>
        <div className="flex h-2 overflow-hidden rounded-full">
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
      </div>

      <p className="mt-4 text-xs text-slate-600">
        Click a photo on the map or use the arrows below to review individual trench
        images.
      </p>

      <div className="mt-4 flex items-center justify-between gap-2 border-t border-slate-100 pt-4">
        <button
          type="button"
          disabled={photos.length === 0}
          onClick={onPrevPhoto}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-40"
          aria-label="Previous photo"
        >
          ←
        </button>
        <span className="text-xs text-slate-600">
          {highlightIndex >= 0
            ? `Photo ${highlightIndex + 1} of ${photos.length}`
            : `${photos.length} photos`}
        </span>
        <button
          type="button"
          disabled={photos.length === 0}
          onClick={onNextPhoto}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-40"
          aria-label="Next photo"
        >
          →
        </button>
      </div>

      {highlightedPhotoId && (
        <button
          type="button"
          onClick={onOpenPhoto}
          className="mt-3 w-full rounded-lg bg-violet-700 px-3 py-2 text-sm font-medium text-white hover:bg-violet-800"
        >
          Open photo detail
        </button>
      )}
    </div>
  );
}
