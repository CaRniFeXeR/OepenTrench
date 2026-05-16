import { useEffect, useState } from 'react';

import type {
  PhotoAnalysisRead,
  PhotoAnalysisReviewUpdate,
  PhotoDocumentationCategory,
} from '../../api/client';
import { reviewProjectImageAnalysisProjectsProjectIdImagesAssetIdAnalysisPatch } from '../../api/client';

type OverrideChoice = 'ai' | 'yes' | 'no';

type ReviewerField =
  | 'reviewer_has_duct'
  | 'reviewer_has_ruler'
  | 'reviewer_is_in_domain'
  | 'reviewer_gps_matches_route'
  | 'reviewer_has_gdpr_problems';

type CriterionRow = {
  emoji: string;
  label: string;
  reviewerField: ReviewerField;
  automated: (a: PhotoAnalysisRead) => boolean;
  invertPrivacy?: boolean;
};

const CRITERIA: CriterionRow[] = [
  {
    emoji: '🧵',
    label: 'Duct visible',
    reviewerField: 'reviewer_has_duct',
    automated: (a) => a.has_duct,
  },
  {
    emoji: '📏',
    label: 'Ruler visible',
    reviewerField: 'reviewer_has_ruler',
    automated: (a) => a.has_ruler,
  },
  {
    emoji: '🏗️',
    label: 'In domain',
    reviewerField: 'reviewer_is_in_domain',
    automated: (a) => a.is_in_domain,
  },
  {
    emoji: '📍',
    label: 'GPS matches route',
    reviewerField: 'reviewer_gps_matches_route',
    automated: (a) => a.gps_matches_route,
  },
  {
    emoji: '🔒',
    label: 'Privacy clear',
    reviewerField: 'reviewer_has_gdpr_problems',
    automated: (a) => !a.has_gdpr_problems,
    invertPrivacy: true,
  },
];

const CATEGORY_LABELS: Record<PhotoDocumentationCategory, string> = {
  green: 'Good',
  yellow: 'Warning',
  red: 'Failed',
};

function choiceFromReviewerValue(
  value: boolean | null | undefined,
  invertPrivacy?: boolean,
): OverrideChoice {
  if (value == null) return 'ai';
  if (invertPrivacy) {
    return value ? 'no' : 'yes';
  }
  return value ? 'yes' : 'no';
}

function reviewerValueFromChoice(
  choice: OverrideChoice,
  invertPrivacy?: boolean,
): boolean | null {
  if (choice === 'ai') return null;
  if (invertPrivacy) {
    return choice === 'no';
  }
  return choice === 'yes';
}

function initialChoices(analysis: PhotoAnalysisRead): Record<ReviewerField, OverrideChoice> {
  return {
    reviewer_has_duct: choiceFromReviewerValue(analysis.reviewer_has_duct),
    reviewer_has_ruler: choiceFromReviewerValue(analysis.reviewer_has_ruler),
    reviewer_is_in_domain: choiceFromReviewerValue(analysis.reviewer_is_in_domain),
    reviewer_gps_matches_route: choiceFromReviewerValue(analysis.reviewer_gps_matches_route),
    reviewer_has_gdpr_problems: choiceFromReviewerValue(
      analysis.reviewer_has_gdpr_problems,
      true,
    ),
  };
}

function buildReviewPayload(
  choices: Record<ReviewerField, OverrideChoice>,
): PhotoAnalysisReviewUpdate {
  const payload: PhotoAnalysisReviewUpdate = { mark_reviewed: true };
  for (const row of CRITERIA) {
    payload[row.reviewerField] = reviewerValueFromChoice(
      choices[row.reviewerField],
      row.invertPrivacy,
    );
  }
  return payload;
}

function toggleOverride(choice: OverrideChoice, aiOk: boolean): OverrideChoice {
  if (choice === 'ai') {
    return aiOk ? 'no' : 'yes';
  }
  return 'ai';
}

function effectivePass(choice: OverrideChoice, aiOk: boolean): boolean {
  if (choice === 'ai') return aiOk;
  return choice === 'yes';
}

function aiChip(ok: boolean): { label: string; className: string } {
  return ok
    ? { label: 'Pass', className: 'border-emerald-200 bg-emerald-50 text-emerald-800' }
    : { label: 'Fail', className: 'border-red-200 bg-red-50 text-red-800' };
}

function CriterionReviewRow({
  row,
  analysis,
  choice,
  compact,
  onToggle,
}: {
  row: CriterionRow;
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
  const [choices, setChoices] = useState(() => initialChoices(analysis));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setChoices(initialChoices(analysis));
    setError(null);
  }, [analysis.asset_id, analysis.updated_at]);

  const submit = async () => {
    setSaving(true);
    setError(null);
    const { error: apiError } =
      await reviewProjectImageAnalysisProjectsProjectIdImagesAssetIdAnalysisPatch({
        path: { project_id: projectId, asset_id: assetId },
        body: buildReviewPayload(choices),
      });
    setSaving(false);
    if (apiError) {
      setError('Could not save review.');
      return;
    }
    await onSaved();
  };

  const aiCategoryLabel = analysis.category
    ? CATEGORY_LABELS[analysis.category]
    : '—';

  return (
    <div className="mt-3">
      <p className={`font-semibold text-slate-900 ${compact ? 'text-xs' : 'text-sm'}`}>
        Review
      </p>
      <p className={`mt-0.5 text-slate-600 ${compact ? 'text-[10px]' : 'text-xs'}`}>
        AI category: <span className="font-medium">{aiCategoryLabel}</span>
        {analysis.reviewed_at && (
          <span className="ml-2 text-slate-500">
            · Reviewed {new Date(analysis.reviewed_at).toLocaleString()}
          </span>
        )}
      </p>
      <p className={`mt-1 text-slate-500 ${compact ? 'text-[10px]' : 'text-xs'}`}>
        Tap a row to disagree with AI; tap again to reset.
      </p>

      <ul className={`mt-2 space-y-1.5 ${compact ? 'space-y-1' : ''}`}>
        {CRITERIA.map((row) => {
          const aiOk = row.automated(analysis);
          const choice = choices[row.reviewerField];
          return (
            <CriterionReviewRow
              key={row.reviewerField}
              row={row}
              analysis={analysis}
              choice={choice}
              compact={compact}
              onToggle={() =>
                setChoices((prev) => ({
                  ...prev,
                  [row.reviewerField]: toggleOverride(choice, aiOk),
                }))
              }
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
        {saving ? 'Saving…' : 'Approve'}
      </button>
    </div>
  );
}

