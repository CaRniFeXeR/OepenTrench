import type {
  PhotoAnalysisRead,
  PhotoDocumentationCategory,
  ProjectAssetRead,
} from '../../api/client';

export const UNASSOCIATED_FCP_ID = '__unassociated__';

export function isUnassociatedFcpId(id: string | null): boolean {
  return id === UNASSOCIATED_FCP_ID;
}

export type TriStateFilter = 'all' | 'yes' | 'no';

export function cycleTriStateFilter(value: TriStateFilter): TriStateFilter {
  if (value === 'all') return 'yes';
  if (value === 'yes') return 'no';
  return 'all';
}

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

export function isUnreviewed(analysis: PhotoAnalysisRead | null | undefined): boolean {
  if (!analysis) return false;
  return analysis.reviewed_at == null;
}

export type PhotoDocumentationCounts = {
  green: number;
  yellow: number;
  red: number;
  pending: number;
  warningNeedsReview: number;
  duplicateCount: number;
};

export function categoryCountsFromAssets(assets: ProjectAssetRead[]): PhotoDocumentationCounts {
  const counts: PhotoDocumentationCounts = {
    green: 0,
    yellow: 0,
    red: 0,
    pending: 0,
    warningNeedsReview: 0,
    duplicateCount: 0,
  };
  for (const asset of assets) {
    if (asset.kind !== 'image') continue;
    if (!asset.analysis) {
      counts.pending += 1;
      continue;
    }
    const cat = analysisEffectiveCategory(asset.analysis);
    if (cat === 'green') counts.green += 1;
    else if (cat === 'yellow') counts.yellow += 1;
    else if (cat === 'red') counts.red += 1;
    if (photoNeedsReview(asset.analysis)) counts.warningNeedsReview += 1;
    if (asset.analysis.effective_is_duplicated) counts.duplicateCount += 1;
  }
  return counts;
}

export function categoryCountsFromAssetsForFcp(
  assets: ProjectAssetRead[],
  fcpId: string,
  assetFcpMap: Map<string, string>,
): PhotoDocumentationCounts {
  const filtered = assets.filter((asset) => {
    if (asset.kind !== 'image') return false;
    if (isUnassociatedFcpId(fcpId)) {
      return !assetFcpMap.has(asset.id);
    }
    return assetFcpMap.get(asset.id) === fcpId;
  });
  return categoryCountsFromAssets(filtered);
}

function matchesTriState(value: boolean, filter: TriStateFilter): boolean {
  if (filter === 'all') return true;
  if (filter === 'yes') return value;
  return !value;
}

function matchesCriteriaFilters(
  analysis: PhotoAnalysisRead,
  options: {
    ductVisible?: TriStateFilter;
    rulerVisible?: TriStateFilter;
    privacyClear?: TriStateFilter;
  },
): boolean {
  if (
    !matchesTriState(analysis.effective_has_duct, options.ductVisible ?? 'all')
  ) {
    return false;
  }
  if (
    !matchesTriState(analysis.effective_has_ruler, options.rulerVisible ?? 'all')
  ) {
    return false;
  }
  if (
    !matchesTriState(
      !analysis.effective_has_gdpr_problems,
      options.privacyClear ?? 'all',
    )
  ) {
    return false;
  }
  return true;
}

export function filterAssetsForDashboard(
  assets: ProjectAssetRead[],
  options: {
    category: PhotoDocumentationCategory;
    unreviewedOnly: boolean;
    fcpId?: string | null;
    assetFcpMap?: Map<string, string>;
    ductVisible?: TriStateFilter;
    rulerVisible?: TriStateFilter;
    privacyClear?: TriStateFilter;
  },
): ProjectAssetRead[] {
  return assets.filter((asset) => {
    if (asset.kind !== 'image' || !asset.analysis) return false;
    if (analysisEffectiveCategory(asset.analysis) !== options.category) return false;
    if (options.unreviewedOnly && !isUnreviewed(asset.analysis)) return false;
    if (!matchesCriteriaFilters(asset.analysis, options)) return false;
    if (options.fcpId != null && options.assetFcpMap) {
      if (isUnassociatedFcpId(options.fcpId)) {
        if (options.assetFcpMap.has(asset.id)) return false;
      } else if (options.assetFcpMap.get(asset.id) !== options.fcpId) {
        return false;
      }
    }
    return true;
  });
}

export function activeCriteriaFilterLabels(options: {
  ductVisible?: TriStateFilter;
  rulerVisible?: TriStateFilter;
  privacyClear?: TriStateFilter;
}): string[] {
  const labels: string[] = [];
  if (options.ductVisible === 'yes') labels.push('duct visible');
  else if (options.ductVisible === 'no') labels.push('duct not visible');
  if (options.rulerVisible === 'yes') labels.push('ruler visible');
  else if (options.rulerVisible === 'no') labels.push('ruler not visible');
  if (options.privacyClear === 'yes') labels.push('privacy clear');
  else if (options.privacyClear === 'no') labels.push('privacy issues');
  return labels;
}
