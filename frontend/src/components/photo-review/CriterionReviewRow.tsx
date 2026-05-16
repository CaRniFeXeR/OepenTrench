import type { PhotoAnalysisRead } from '../../api/client';
import {
  aiChip,
  effectivePass,
  type OverrideChoice,
  type PhotoReviewCriterion,
} from './photoReviewCriteria';

export function CriterionReviewRow({
  row,
  analysis,
  choice,
  compact,
  onToggle,
}: {
  row: PhotoReviewCriterion;
  analysis: PhotoAnalysisRead;
  choice: OverrideChoice;
  compact?: boolean;
  onToggle: () => void;
}) {
  const aiOk = row.automated(analysis);
  const overridden = choice !== 'ai';
  const chip = aiChip(aiOk);
  const reviewerPass = effectivePass(choice, aiOk);
  const reviewerChip = aiChip(reviewerPass);

  return (
    <li>
      <button
        type="button"
        onClick={onToggle}
        className={`flex w-full items-center gap-2 rounded-lg border px-2 py-2 text-left transition-colors ${
          compact ? 'py-1.5' : 'py-2'
        } ${
          overridden
            ? 'border-violet-300 bg-violet-50/60 ring-1 ring-violet-300'
            : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
        }`}
        title={
          overridden
            ? 'Click to reset and agree with AI'
            : 'Click to override AI prediction'
        }
      >
        <span className={compact ? 'text-base' : 'text-lg'} aria-hidden>
          {row.emoji}
        </span>
        <span
          className={`min-w-0 flex-1 font-medium text-slate-800 ${
            compact ? 'text-xs' : 'text-sm'
          }`}
        >
          {row.label}
        </span>
        <span
          className={`shrink-0 rounded-md border px-1.5 py-0.5 font-medium ${
            compact ? 'text-[10px]' : 'text-xs'
          } ${chip.className}`}
        >
          AI: {chip.label}
        </span>
        {overridden && (
          <span
            className={`shrink-0 rounded-md border px-1.5 py-0.5 font-medium ${
              compact ? 'text-[10px]' : 'text-xs'
            } ${reviewerChip.className}`}
          >
            You: {reviewerChip.label}
          </span>
        )}
      </button>
    </li>
  );
}
