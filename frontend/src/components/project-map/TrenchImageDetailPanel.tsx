import type { ProjectAssetRead } from '../../api/client';
import { AnalysisTagRow, qualityBadge } from '../project-images/analysisDisplay';
import { PanelBackLink } from '../ui/PanelBackLink';
import { PhotoStepper } from '../ui/PhotoStepper';
import { projectImageContentUrl } from './imageContentUrl';

export function TrenchImageDetailPanel({
  projectId,
  asset,
  fcpCode,
  photoIndex,
  photoTotal,
  onBack,
  onPrev,
  onNext,
}: {
  projectId: string;
  asset: ProjectAssetRead;
  fcpCode: string;
  photoIndex: number;
  photoTotal: number;
  onBack: () => void;
  onPrev: () => void;
  onNext: () => void;
}) {
  const analysis = asset.analysis;
  const badge = qualityBadge(analysis);
  const imageUrl = projectImageContentUrl(projectId, asset.id);

  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-4">
      <PanelBackLink label="← Back to FCP" onClick={onBack} />

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

      <button
        type="button"
        disabled
        title="False call override API is not available yet."
        className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        Flag as False Call
      </button>

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
