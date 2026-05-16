import type { PhotoDocumentationCategory } from '../../../api/client';
import { photoDocCategoryFilterLabel } from '../../project-images/photoDocumentationCategories';
import { activeCriteriaFilterLabels, type TriStateFilter } from '../../project-images/photoDocumentationUtils';

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
  criteriaFilters?: {
    ductVisible?: TriStateFilter;
    rulerVisible?: TriStateFilter;
    privacyClear?: TriStateFilter;
  },
): string {
  const label = photoDocCategoryFilterLabel(category);
  const fcpPart = fcpCode ? ` in ${fcpCode}` : '';
  const criteriaLabels = criteriaFilters
    ? activeCriteriaFilterLabels(criteriaFilters)
    : [];
  const criteriaPart =
    criteriaLabels.length > 0 ? ` matching ${criteriaLabels.join(', ')}` : '';

  if (unreviewedOnly) {
    return `No unreviewed ${label} photos${fcpPart}${criteriaPart}.`;
  }
  return `No ${label} photos${fcpPart}${criteriaPart}.`;
}
