import { useEffect, useState, type ReactNode } from 'react';

import type { ProjectAssetRead } from '../../api/client';
import { PhotoReviewSection } from '../photo-review/PhotoReviewSection';
import { qualityBadge } from '../project-images/analysisDisplay';
import { projectImageContentUrl } from '../project-map/imageContentUrl';

function FullscreenIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className="h-4 w-4"
      aria-hidden
    >
      <path d="M3 3a1 1 0 0 0-1 1v3a1 1 0 1 0 2 0V6.414l2.293 2.293a1 1 0 0 0 1.414-1.414L5.414 5H7a1 1 0 1 0 0-2H4a1 1 0 0 0-1 1Zm14 0a1 1 0 0 0-1 1v3a1 1 0 0 0 2 0V6.414l-2.293 2.293a1 1 0 0 0 1.414 1.414L14.586 5H13a1 1 0 1 0 0-2h3a1 1 0 0 0 1-1ZM3 17a1 1 0 0 0 1 1h3a1 1 0 1 0 0-2H6.414l2.293-2.293a1 1 0 0 0-1.414-1.414L5 15.586V14a1 1 0 1 0-2 0v3a1 1 0 0 0 1 1Zm14 0a1 1 0 0 0-1-1v-3a1 1 0 0 0-2 0v1.586l-2.293-2.293a1 1 0 0 0-1.414 1.414L15.586 15H14a1 1 0 1 0 0 2h3a1 1 0 0 0 1-1Z" />
    </svg>
  );
}

function PhotoReviewModal({
  imageUrl,
  label,
  badge,
  onClose,
  children,
}: {
  imageUrl: string;
  label: string;
  badge: { label: string; className: string };
  onClose: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose();
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="presentation"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="photo-review-modal-title"
        className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-y-auto rounded-xl bg-white p-4 shadow-xl sm:p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-start justify-between gap-3">
          <p
            id="photo-review-modal-title"
            className="min-w-0 flex-1 truncate text-sm font-medium text-slate-900"
            title={label}
          >
            {label}
          </p>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-lg px-2 py-1 text-sm text-slate-600 hover:bg-slate-100"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="relative rounded-lg bg-slate-100">
          <img
            src={imageUrl}
            alt={label}
            className="max-h-[min(70vh,720px)] w-full object-contain"
          />
          <span
            className={`absolute bottom-2 left-2 z-10 inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold shadow-sm ring-1 ring-black/10 ${badge.className}`}
          >
            {badge.label}
          </span>
        </div>

        <div className="mt-4">{children}</div>
      </div>
    </div>
  );
}

export function PhotoReviewCard({
  projectId,
  asset,
  onSaved,
}: {
  projectId: string;
  asset: ProjectAssetRead;
  onSaved: () => Promise<void>;
}) {
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
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

        <p
          className="absolute left-2 top-2 z-10 max-w-[calc(100%-3rem)] truncate rounded-md bg-black/55 px-2 py-0.5 text-xs text-white"
          title={asset.original_label}
        >
          {asset.original_label}
        </p>

        <button
          type="button"
          onClick={() => setReviewModalOpen(true)}
          className="absolute right-2 top-2 z-10 flex items-center justify-center rounded-full bg-white/90 p-1.5 text-slate-700 shadow hover:bg-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-600"
          aria-label="Open fullscreen review"
        >
          <FullscreenIcon />
        </button>

        <span
          className={`absolute bottom-2 left-2 z-10 inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold shadow-sm ring-1 ring-black/10 ${badge.className}`}
        >
          {badge.label}
        </span>
      </div>

      <div className="flex flex-1 flex-col p-3">
        {analysis ? (
          <PhotoReviewSection
            projectId={projectId}
            assetId={asset.id}
            analysis={analysis}
            onSaved={onSaved}
            compact
          />
        ) : (
          <p className="text-xs text-slate-500">Analysis pending</p>
        )}
      </div>

      {reviewModalOpen && (
        <PhotoReviewModal
          imageUrl={imageUrl}
          label={asset.original_label}
          badge={badge}
          onClose={() => setReviewModalOpen(false)}
        >
          {analysis ? (
            <PhotoReviewSection
              projectId={projectId}
              assetId={asset.id}
              analysis={analysis}
              onSaved={onSaved}
            />
          ) : (
            <p className="text-sm text-slate-500">Analysis pending</p>
          )}
        </PhotoReviewModal>
      )}
    </article>
  );
}
