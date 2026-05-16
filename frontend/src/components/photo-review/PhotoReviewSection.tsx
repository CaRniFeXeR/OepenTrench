import type { PhotoAnalysisRead } from '../../api/client';
import { CriterionReviewRow } from './CriterionReviewRow';
import { usePhotoReviewForm } from './usePhotoReviewForm';

export function PhotoReviewSection({
  projectId,
  assetId,
  analysis,
  onSaved,
  compact = false,
}: {
  projectId: string;
  assetId: string;
  analysis: PhotoAnalysisRead;
  onSaved: () => Promise<void>;
  compact?: boolean;
}) {
  const { choices, saving, error, criteria, toggleCriterion, submit } = usePhotoReviewForm({
    projectId,
    assetId,
    analysis,
    onSaved,
  });

  return (
    <div className="mt-3">
      <p className={`font-semibold text-slate-900 ${compact ? 'text-xs' : 'text-sm'}`}>
        Review
      </p>

      <ul className={`mt-2 space-y-1.5 ${compact ? 'space-y-1' : ''}`}>
        {criteria.map((row) => {
          const aiOk = row.automated(analysis);
          const choice = choices[row.reviewerField];
          return (
            <CriterionReviewRow
              key={row.reviewerField}
              row={row}
              analysis={analysis}
              choice={choice}
              compact={compact}
              onToggle={() => toggleCriterion(row.reviewerField, aiOk)}
            />
          );
        })}
      </ul>

      {error && <p className="mt-2 text-xs text-red-700">{error}</p>}

      <button
        type="button"
        disabled={saving}
        onClick={() => submit()}
        className={`mt-3 w-full rounded-lg bg-violet-700 font-medium text-white hover:bg-violet-800 disabled:opacity-60 ${
          compact ? 'px-3 py-1.5 text-xs' : 'px-3 py-2 text-sm'
        }`}
      >
        {saving ? 'Saving…' : 'Submit'}
      </button>
    </div>
  );
}
