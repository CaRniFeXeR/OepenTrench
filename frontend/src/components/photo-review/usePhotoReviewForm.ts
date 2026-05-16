import { useEffect, useState } from 'react';

import type { PhotoAnalysisRead } from '../../api/client';
import { reviewProjectImageAnalysisProjectsProjectIdImagesAssetIdAnalysisPatch } from '../../api/client';
import {
  buildReviewPayload,
  initialChoices,
  toggleOverride,
  type OverrideChoice,
  type ReviewerField,
  PHOTO_REVIEW_CRITERIA,
} from './photoReviewCriteria';

export function usePhotoReviewForm({
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

  const toggleCriterion = (field: ReviewerField, aiOk: boolean) => {
    setChoices((prev) => ({
      ...prev,
      [field]: toggleOverride(prev[field], aiOk),
    }));
  };

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

  return {
    choices,
    saving,
    error,
    criteria: PHOTO_REVIEW_CRITERIA,
    toggleCriterion,
    submit,
  };
}

export type { OverrideChoice };
