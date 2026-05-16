import type {
  PhotoAnalysisRead,
  PhotoDocumentationCategory,
  ProjectAssetRead,
} from '../../api/client';

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
};

export function categoryCountsFromAssets(assets: ProjectAssetRead[]): PhotoDocumentationCounts {
  const counts: PhotoDocumentationCounts = {
    green: 0,
    yellow: 0,
    red: 0,
    pending: 0,
    warningNeedsReview: 0,
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
  }
  return counts;
}

export function categoryCountsFromAssetsForFcp(
  assets: ProjectAssetRead[],
  fcpId: string,
  assetFcpMap: Map<string, string>,
): PhotoDocumentationCounts {
  const filtered = assets.filter(
    (asset) => asset.kind === 'image' && assetFcpMap.get(asset.id) === fcpId,
  );
  return categoryCountsFromAssets(filtered);
}

export function filterAssetsForDashboard(
  assets: ProjectAssetRead[],
  options: {
    category: PhotoDocumentationCategory;
    unreviewedOnly: boolean;
    fcpId?: string | null;
    assetFcpMap?: Map<string, string>;
  },
): ProjectAssetRead[] {
  return assets.filter((asset) => {
    if (asset.kind !== 'image' || !asset.analysis) return false;
    if (analysisEffectiveCategory(asset.analysis) !== options.category) return false;
    if (options.unreviewedOnly && !isUnreviewed(asset.analysis)) return false;
    if (options.fcpId != null && options.assetFcpMap) {
      if (options.assetFcpMap.get(asset.id) !== options.fcpId) return false;
    }
    return true;
  });
}
