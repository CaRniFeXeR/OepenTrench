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
  label: string;
  reviewerField: ReviewerField;
  automated: (a: PhotoAnalysisRead) => boolean;
  invertPrivacy?: boolean;
};

const CRITERIA: CriterionRow[] = [
  {
    label: 'Duct visible',
    reviewerField: 'reviewer_has_duct',
    automated: (a) => a.has_duct,
  },
  {
    label: 'Ruler visible',
    reviewerField: 'reviewer_has_ruler',
    automated: (a) => a.has_ruler,
  },
  {
    label: 'In domain',
    reviewerField: 'reviewer_is_in_domain',
    automated: (a) => a.is_in_domain,
  },
  {
    label: 'GPS matches route',
    reviewerField: 'reviewer_gps_matches_route',
    automated: (a) => a.gps_matches_route,
  },
  {
    label: 'Privacy clear',
    reviewerField: 'reviewer_has_gdpr_problems',
    automated: (a) => !a.has_gdpr_problems,
    invertPrivacy: true,
  },
];

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
  options?: { categoryOverride?: PhotoDocumentationCategory | null },
): PhotoAnalysisReviewUpdate {
  const payload: PhotoAnalysisReviewUpdate = { mark_reviewed: true };
  for (const row of CRITERIA) {
    payload[row.reviewerField] = reviewerValueFromChoice(
      choices[row.reviewerField],
      row.invertPrivacy,
    );
  }
  if (options && 'categoryOverride' in options) {
    payload.reviewer_override_category = options.categoryOverride ?? null;
  }
  return payload;
}

function OverrideToggle({
  value,
  onChange,
}: {
  value: OverrideChoice;
  onChange: (v: OverrideChoice) => void;
}) {
  const options: { id: OverrideChoice; label: string }[] = [
    { id: 'ai', label: 'AI' },
    { id: 'yes', label: 'Yes' },
    { id: 'no', label: 'No' },
  ];
  return (
    <div className="inline-flex rounded-md border border-slate-200 bg-slate-50 p-0.5 text-xs">
      {options.map((opt) => (
        <button
          key={opt.id}
          type="button"
          onClick={() => onChange(opt.id)}
          className={`rounded px-2 py-1 ${
            value === opt.id
              ? 'bg-white font-medium text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

export function PhotoReviewSection({
  projectId,
  assetId,
  analysis,
  onSaved,
}: {
  projectId: string;
  assetId: string;
  analysis: PhotoAnalysisRead;
  onSaved: () => Promise<void>;
}) {
  const [choices, setChoices] = useState(() => initialChoices(analysis));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setChoices(initialChoices(analysis));
    setError(null);
  }, [analysis.asset_id, analysis.updated_at]);

  const submit = async (options?: { categoryOverride?: PhotoDocumentationCategory | null }) => {
    setSaving(true);
    setError(null);
    const { error: apiError } =
      await reviewProjectImageAnalysisProjectsProjectIdImagesAssetIdAnalysisPatch({
        path: { project_id: projectId, asset_id: assetId },
        body: buildReviewPayload(choices, options),
      });
    setSaving(false);
    if (apiError) {
      setError('Could not save review.');
      return;
    }
    await onSaved();
  };

  const showWarningWorkflow =
    analysis.effective_category === 'yellow' || analysis.category === 'yellow';

  return (
    <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p className="text-sm font-semibold text-slate-900">Review documentation</p>
      <p className="mt-1 text-xs text-slate-600">
        Automated category: <span className="font-medium">{analysis.category ?? '—'}</span>
        {analysis.reviewed_at && (
          <span className="ml-2 text-slate-500">
            Reviewed {new Date(analysis.reviewed_at).toLocaleString()}
          </span>
        )}
      </p>

      <ul className="mt-3 space-y-2">
        {CRITERIA.map((row) => {
          const aiOk = row.automated(analysis);
          return (
            <li
              key={row.reviewerField}
              className="flex flex-col gap-1 rounded-md bg-white px-2 py-2 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0">
                <span className="text-sm text-slate-800">{row.label}</span>
                <span className="ml-2 text-xs text-slate-500">
                  AI: {aiOk ? 'yes' : 'no'}
                </span>
              </div>
              <OverrideToggle
                value={choices[row.reviewerField]}
                onChange={(v) =>
                  setChoices((prev) => ({ ...prev, [row.reviewerField]: v }))
                }
              />
            </li>
          );
        })}
      </ul>

      {error && <p className="mt-2 text-xs text-red-700">{error}</p>}

      <div className="mt-3 flex flex-col gap-2">
        <button
          type="button"
          disabled={saving}
          onClick={() => submit()}
          className="w-full rounded-lg bg-violet-700 px-3 py-2 text-sm font-medium text-white hover:bg-violet-800 disabled:opacity-60"
        >
          {saving ? 'Saving…' : showWarningWorkflow ? 'Approve' : 'Save review'}
        </button>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={saving}
            onClick={() => submit({ categoryOverride: 'green' })}
            className="flex-1 rounded-lg border border-emerald-300 bg-emerald-50 px-2 py-1.5 text-xs font-medium text-emerald-900 hover:bg-emerald-100 disabled:opacity-60"
          >
            Approve as Good
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => submit({ categoryOverride: 'red' })}
            className="flex-1 rounded-lg border border-red-300 bg-red-50 px-2 py-1.5 text-xs font-medium text-red-900 hover:bg-red-100 disabled:opacity-60"
          >
            Mark Failed
          </button>
        </div>
      </div>
    </div>
  );
}
