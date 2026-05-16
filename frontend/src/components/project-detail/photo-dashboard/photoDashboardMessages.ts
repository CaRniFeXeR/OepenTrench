import type { PhotoDocumentationCategory } from '../../../api/client';
import { photoDocCategoryFilterLabel } from '../../project-images/photoDocumentationCategories';

export function warningApprovalLabel(needsReview: number, yellowTotal: number): string {
  const noun = needsReview === 1 ? 'needs' : 'need';
  if (needsReview < yellowTotal) {
    return `${needsReview} of ${yellowTotal} ${noun} approval`;
  }
  return `${needsReview} ${noun} approval`;
}

export function emptyMessage(
  category: PhotoDocumentationCategory,
  unreviewedOnly: boolean,
  fcpCode: string | null,
): string {
  const label = photoDocCategoryFilterLabel(category);
  const fcpPart = fcpCode ? ` in ${fcpCode}` : '';
  if (unreviewedOnly) {
    return `No unreviewed ${label} photos${fcpPart}.`;
  }
  return `No ${label} photos${fcpPart}.`;
}
