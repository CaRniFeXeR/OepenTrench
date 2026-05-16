import type { ProjectAssetRead } from '../../api/client';
import { qualityBadge } from '../project-images/analysisDisplay';
import { projectImageContentUrl } from '../project-map/imageContentUrl';
import { PhotoReviewSection } from '../project-map/PhotoReviewSection';

export function PhotoReviewCard({
  projectId,
  asset,
  onSaved,
}: {
  projectId: string;
  asset: ProjectAssetRead;
  onSaved: () => Promise<void>;
}) {
  const analysis = asset.analysis;
  const badge = qualityBadge(analysis, { pendingWhenNull: true });
  const imageUrl = projectImageContentUrl(projectId, asset.id);

  return (
    <article className="flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="relative bg-slate-100">
        <img
          src={imageUrl}
          alt={asset.original_label}
          className="aspect-[4/3] w-full object-contain"
        />
      </div>

      <div className="flex flex-1 flex-col p-3">
        <p
          className="line-clamp-1 text-xs text-slate-500"
          title={asset.original_label}
        >
          {asset.original_label}
        </p>

        <p
          className={`mt-2 inline-flex w-fit rounded-full px-2.5 py-0.5 text-xs font-semibold ${badge.className}`}
        >
          {badge.label}
        </p>

        {analysis ? (
          <PhotoReviewSection
            projectId={projectId}
            assetId={asset.id}
            analysis={analysis}
            onSaved={onSaved}
            compact
          />
        ) : (
          <p className="mt-3 text-xs text-slate-500">Analysis pending</p>
        )}
      </div>
    </article>
  );
}
