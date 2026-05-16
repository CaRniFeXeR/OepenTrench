import type { MapPhotoMarkerRead } from '../../api/client';
import { DocumentationStatusBarFromCounts } from '../ui/DocumentationStatusBar';
import { PanelBackLink } from '../ui/PanelBackLink';
import { PhotoStepper } from '../ui/PhotoStepper';
import { categoryCounts } from './mapPhotoUtils';

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
  const highlightIndex = highlightedPhotoId
    ? photos.findIndex((p) => p.asset_id === highlightedPhotoId)
    : -1;

  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-4">
      <PanelBackLink label="← Back to project" onClick={onBack} />

      <h2 className="text-lg font-semibold text-slate-900">{fcpCode}</h2>
      <p className="text-sm text-slate-600">{fcpLabel}</p>
      <p className="mt-1 text-xs text-slate-500">Cluster / project: {projectName}</p>

      <dl className="mt-4 text-sm text-slate-700">
        <dt className="text-slate-500">Photos in FCP</dt>
        <dd className="font-medium">{photos.length} documented</dd>
      </dl>

      <div className="mt-4">
        <p className="mb-1 text-xs font-medium text-slate-600">Status in this FCP</p>
        <DocumentationStatusBarFromCounts counts={counts} />
      </div>

      <p className="mt-4 text-xs text-slate-600">
        Click a photo on the map or use the arrows below to review individual trench
        images.
      </p>

      <PhotoStepper
        variant="compact"
        photoIndex={highlightIndex}
        photoTotal={photos.length}
        onPrev={onPrevPhoto}
        onNext={onNextPhoto}
      />

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
