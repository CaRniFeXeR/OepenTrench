import type { PhotoAnalysisRead, ProjectAssetRead } from '../../api/client';
import { projectImageContentUrl } from './imageContentUrl';
import { effectiveCategory } from './mapPhotoUtils';

function qualityBadge(analysis: PhotoAnalysisRead | null | undefined): {
  label: string;
  className: string;
} {
  const cat = analysis
    ? effectiveCategory(
        analysis.reviewer_override_category ?? analysis.category ?? null,
      )
    : 'unknown';
  if (cat === 'green') {
    return { label: 'Good', className: 'bg-emerald-100 text-emerald-800' };
  }
  if (cat === 'yellow') {
    return { label: 'Poor', className: 'bg-amber-100 text-amber-900' };
  }
  return { label: 'Missing', className: 'bg-red-100 text-red-800' };
}

function AnalysisTag({
  label,
  ok,
}: {
  label: string;
  ok: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs ${
        ok
          ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
          : 'border-red-200 bg-red-50 text-red-800'
      }`}
    >
      {ok ? '✓' : '✗'} {label}
    </span>
  );
}

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
      <button
        type="button"
        onClick={onBack}
        className="mb-3 text-left text-sm font-medium text-violet-700 hover:text-violet-900"
      >
        ← Back to FCP
      </button>

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
        <div className="mt-4 flex flex-wrap gap-2">
          <AnalysisTag label="Duct visible" ok={analysis.has_duct} />
          <AnalysisTag label="Sand bedding" ok={analysis.has_sand_bedding} />
          <AnalysisTag label="Burial depth / ruler" ok={analysis.has_ruler} />
          <AnalysisTag label="Pipe end seal" ok={analysis.has_pipe_end_seal} />
          <AnalysisTag label="GPS match" ok={analysis.gps_matches_route} />
          <AnalysisTag label="Date valid" ok={analysis.date_valid} />
          <AnalysisTag label="Privacy clear" ok={!analysis.has_gdpr_problems} />
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

      <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-600">
        <button type="button" onClick={onPrev} className="font-medium text-violet-700 hover:underline">
          ← Previous photo
        </button>
        <span>
          Photo {photoIndex + 1} of {photoTotal} in {fcpCode}
        </span>
        <button type="button" onClick={onNext} className="font-medium text-violet-700 hover:underline">
          Next photo →
        </button>
      </div>
    </div>
  );
}
