import { useEffect, useState } from 'react';

import type { PhotoAnalysisRead } from '../../api/client';
import { reviewProjectImageAnalysisProjectsProjectIdImagesAssetIdAnalysisPatch } from '../../api/client';
import { aiChip } from './photoReviewCriteria';

export type DuplicateOverrideChoice = 'ai' | 'not_duplicate' | 'duplicate';

export function duplicateChoiceFromReviewer(
  value: boolean | null | undefined,
): DuplicateOverrideChoice {
  if (value == null) return 'ai';
  return value ? 'duplicate' : 'not_duplicate';
}

export function reviewerFromDuplicateChoice(
  choice: DuplicateOverrideChoice,
): boolean | null {
  if (choice === 'ai') return null;
  if (choice === 'duplicate') return true;
  return false;
}

export function toggleDuplicateChoice(
  choice: DuplicateOverrideChoice,
  aiNotDuplicate: boolean,
): DuplicateOverrideChoice {
  if (choice === 'ai') {
    return aiNotDuplicate ? 'duplicate' : 'not_duplicate';
  }
  return 'ai';
}

export function duplicateEffectivePass(
  choice: DuplicateOverrideChoice,
  aiNotDuplicate: boolean,
): boolean {
  if (choice === 'ai') return aiNotDuplicate;
  return choice === 'not_duplicate';
}

export function useDuplicateOverride({
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
  const aiNotDuplicate = !analysis.is_duplicated;
  const [choice, setChoice] = useState(() =>
    duplicateChoiceFromReviewer(analysis.reviewer_is_duplicated),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setChoice(duplicateChoiceFromReviewer(analysis.reviewer_is_duplicated));
    setError(null);
  }, [analysis.asset_id, analysis.updated_at, analysis.reviewer_is_duplicated]);

  const toggle = async () => {
    const next = toggleDuplicateChoice(choice, aiNotDuplicate);
    setChoice(next);
    setSaving(true);
    setError(null);
    const { error: apiError } =
      await reviewProjectImageAnalysisProjectsProjectIdImagesAssetIdAnalysisPatch({
        path: { project_id: projectId, asset_id: assetId },
        body: {
          reviewer_is_duplicated: reviewerFromDuplicateChoice(next),
          mark_reviewed: false,
        },
      });
    setSaving(false);
    if (apiError) {
      setChoice(duplicateChoiceFromReviewer(analysis.reviewer_is_duplicated));
      setError('Could not save duplicate override.');
      return;
    }
    await onSaved();
  };

  const overridden = choice !== 'ai';
  const aiChipState = aiChip(aiNotDuplicate);
  const reviewerPass = duplicateEffectivePass(choice, aiNotDuplicate);
  const reviewerChipState = aiChip(reviewerPass);

  return {
    choice,
    saving,
    error,
    overridden,
    aiNotDuplicate,
    aiChipState,
    reviewerChipState,
    effectiveIsDuplicated: analysis.effective_is_duplicated,
    toggle,
  };
}
