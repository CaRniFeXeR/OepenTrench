import type { ProjectAssetRead } from '../../api/client';
import { AnalysisTagRow, qualityBadge } from '../project-images/analysisDisplay';
import { PanelBackLink } from '../ui/PanelBackLink';
import { PhotoStepper } from '../ui/PhotoStepper';
import { projectImageContentUrl } from './imageContentUrl';
import { PhotoReviewSection } from './PhotoReviewSection';

export function TrenchImageDetailPanel({
  projectId,
  asset,
  fcpCode,
  photoIndex,
  photoTotal,
  reviewQueueMode,
  onBack,
  onPrev,
  onNext,
  onReviewSaved,
}: {
  projectId: string;
  asset: ProjectAssetRead;
  fcpCode: string;
  photoIndex: number;
  photoTotal: number;
  reviewQueueMode?: boolean;
  onBack: () => void;
  onPrev: () => void;
  onNext: () => void;
  onReviewSaved: () => Promise<void>;
}) {
  const analysis = asset.analysis;
  const badge = qualityBadge(analysis);
  const imageUrl = projectImageContentUrl(projectId, asset.id);

  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-4">
      <PanelBackLink label="← Back to FCP" onClick={onBack} />

      {reviewQueueMode && (
        <p className="mb-2 rounded-md bg-orange-50 px-2 py-1 text-xs font-medium text-orange-900">
          Warning review queue — {photoTotal} photo{photoTotal === 1 ? '' : 's'} remaining
        </p>
      )}

      <div className="relative flex items-center justify-center rounded-lg bg-slate-100">
        <button
          type="button"
          onClick={onPrev}
          className="absolute left-2 z-10 rounded-full bg-white/90 px-2 py-1 text-lg shadow hover:bg-white"
          aria-label="Previous photo"
        >
          ‹
        </button>
        <img
          src={imageUrl}
          alt={asset.original_label}
          className="max-h-64 w-full object-contain"
        />
        <button
          type="button"
          onClick={onNext}
          className="absolute right-2 z-10 rounded-full bg-white/90 px-2 py-1 text-lg shadow hover:bg-white"
          aria-label="Next photo"
        >
          ›
        </button>
      </div>

      <p
        className={`mt-3 inline-flex w-fit rounded-full px-3 py-1 text-sm font-semibold ${badge.className}`}
      >
        {badge.label}
      </p>

      {analysis && (
        <div className="mt-4">
          <AnalysisTagRow analysis={analysis} />
        </div>
      )}

      {analysis && (
        <PhotoReviewSection
          projectId={projectId}
          assetId={asset.id}
          analysis={analysis}
          onSaved={onReviewSaved}
        />
      )}

      <PhotoStepper
        variant="footer"
        photoIndex={photoIndex}
        photoTotal={photoTotal}
        contextLabel={fcpCode}
        onPrev={onPrev}
        onNext={onNext}
      />
    </div>
  );
}
