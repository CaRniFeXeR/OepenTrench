import type {
  PhotoAnalysisRead,
  PhotoAnalysisReviewUpdate,
} from '../../api/client';

export type OverrideChoice = 'ai' | 'yes' | 'no';

export type ReviewerField =
  | 'reviewer_has_duct'
  | 'reviewer_has_ruler'
  | 'reviewer_is_in_domain'
  | 'reviewer_gps_matches_route'
  | 'reviewer_has_gdpr_problems';

export type PhotoReviewCriterion = {
  key: string;
  emoji: string;
  label: string;
  shortLabel: string;
  reviewerField: ReviewerField;
  automated: (a: PhotoAnalysisRead) => boolean;
  effective: (a: PhotoAnalysisRead) => boolean;
  overridden: (a: PhotoAnalysisRead) => boolean;
  invertPrivacy?: boolean;
};

export const PHOTO_REVIEW_CRITERIA: PhotoReviewCriterion[] = [
  {
    key: 'duct',
    emoji: '🧵',
    label: 'Duct visible',
    shortLabel: 'Duct',
    reviewerField: 'reviewer_has_duct',
    automated: (a) => a.has_duct,
    effective: (a) => a.effective_has_duct,
    overridden: (a) => a.reviewer_has_duct != null,
  },
  {
    key: 'ruler',
    emoji: '📏',
    label: 'Ruler visible',
    shortLabel: 'Ruler',
    reviewerField: 'reviewer_has_ruler',
    automated: (a) => a.has_ruler,
    effective: (a) => a.effective_has_ruler,
    overridden: (a) => a.reviewer_has_ruler != null,
  },
  {
    key: 'domain',
    emoji: '🏗️',
    label: 'In domain',
    shortLabel: 'Domain',
    reviewerField: 'reviewer_is_in_domain',
    automated: (a) => a.is_in_domain,
    effective: (a) => a.effective_is_in_domain,
    overridden: (a) => a.reviewer_is_in_domain != null,
  },
  {
    key: 'gps',
    emoji: '📍',
    label: 'GPS matches route',
    shortLabel: 'GPS',
    reviewerField: 'reviewer_gps_matches_route',
    automated: (a) => a.gps_matches_route,
    effective: (a) => a.effective_gps_matches_route,
    overridden: (a) => a.reviewer_gps_matches_route != null,
  },
  {
    key: 'privacy',
    emoji: '🔒',
    label: 'Privacy clear',
    shortLabel: 'Privacy',
    reviewerField: 'reviewer_has_gdpr_problems',
    automated: (a) => !a.has_gdpr_problems,
    effective: (a) => !a.effective_has_gdpr_problems,
    overridden: (a) => a.reviewer_has_gdpr_problems != null,
    invertPrivacy: true,
  },
];

export const READONLY_ANALYSIS_TAGS: {
  key: string;
  full: string;
  short: string;
  ok: (a: PhotoAnalysisRead) => boolean;
  overridden: (a: PhotoAnalysisRead) => boolean;
}[] = [
  ...PHOTO_REVIEW_CRITERIA.map((c) => ({
    key: c.key,
    full: c.label,
    short: c.shortLabel,
    ok: c.effective,
    overridden: c.overridden,
  })),
  {
    key: 'date',
    full: 'Date valid',
    short: 'Date',
    ok: (a) => a.date_valid,
    overridden: () => false,
  },
];

export function choiceFromReviewerValue(
  value: boolean | null | undefined,
  invertPrivacy?: boolean,
): OverrideChoice {
  if (value == null) return 'ai';
  if (invertPrivacy) {
    return value ? 'no' : 'yes';
  }
  return value ? 'yes' : 'no';
}

export function reviewerValueFromChoice(
  choice: OverrideChoice,
  invertPrivacy?: boolean,
): boolean | null {
  if (choice === 'ai') return null;
  if (invertPrivacy) {
    return choice === 'no';
  }
  return choice === 'yes';
}

export function initialChoices(
  analysis: PhotoAnalysisRead,
): Record<ReviewerField, OverrideChoice> {
  const choices = {} as Record<ReviewerField, OverrideChoice>;
  for (const row of PHOTO_REVIEW_CRITERIA) {
    choices[row.reviewerField] = choiceFromReviewerValue(
      analysis[row.reviewerField],
      row.invertPrivacy,
    );
  }
  return choices;
}

export function buildReviewPayload(
  choices: Record<ReviewerField, OverrideChoice>,
): PhotoAnalysisReviewUpdate {
  const payload: PhotoAnalysisReviewUpdate = { mark_reviewed: true };
  for (const row of PHOTO_REVIEW_CRITERIA) {
    payload[row.reviewerField] = reviewerValueFromChoice(
      choices[row.reviewerField],
      row.invertPrivacy,
    );
  }
  return payload;
}

export function toggleOverride(choice: OverrideChoice, aiOk: boolean): OverrideChoice {
  if (choice === 'ai') {
    return aiOk ? 'no' : 'yes';
  }
  return 'ai';
}

export function effectivePass(choice: OverrideChoice, aiOk: boolean): boolean {
  if (choice === 'ai') return aiOk;
  return choice === 'yes';
}

export function aiChip(ok: boolean): { label: string; className: string } {
  return ok
    ? { label: '✓', className: 'border-emerald-200 bg-emerald-50 text-emerald-800' }
    : { label: '✗', className: 'border-red-200 bg-red-50 text-red-800' };
}
