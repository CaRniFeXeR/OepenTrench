import type { PhotoAnalysisRead, PhotoDocumentationCategory } from '../../api/client';

export function analysisEffectiveCategory(
  analysis: PhotoAnalysisRead | null | undefined,
): PhotoDocumentationCategory | 'unknown' {
  if (!analysis) return 'unknown';
  return analysis.effective_category ?? 'unknown';
}

export function photoNeedsReview(analysis: PhotoAnalysisRead | null | undefined): boolean {
  if (!analysis) return false;
  return analysis.effective_category === 'yellow' && analysis.reviewed_at == null;
}
