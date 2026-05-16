import type {
  FcpCoverageRead,
  PhotoDocumentationCategory,
  ProjectAssetRead,
} from '../../../api/client';
import { PHOTO_REVIEW_CRITERIA } from '../../photo-review/photoReviewCriteria';
import {
  analysisEffectiveCategory,
  categoryCountsFromAssets,
  isUnassociatedFcpId,
} from '../../project-images/photoDocumentationUtils';
import { categoryPercentages } from '../../ui/DocumentationStatusBar';

export type ReportCategoryStats = {
  green: number;
  yellow: number;
  red: number;
  pending: number;
  greenPct: number;
  yellowPct: number;
  redPct: number;
};

export type ReportPredictionStat = {
  key: string;
  label: string;
  emoji: string;
  pass: number;
  total: number;
  pct: number;
};

export type ReportCoverageDetail = {
  coverageRatio: number;
  coveredCount: number;
  compartmentCount: number;
} | null;

export function filterScopeAssets(
  assets: ProjectAssetRead[],
  assetFcpMap: Map<string, string>,
  fcpId?: string | null,
): ProjectAssetRead[] {
  if (fcpId == null) {
    return assets.filter((a) => a.kind === 'image');
  }
  return assets.filter((asset) => {
    if (asset.kind !== 'image') return false;
    if (isUnassociatedFcpId(fcpId)) {
      return !assetFcpMap.has(asset.id);
    }
    return assetFcpMap.get(asset.id) === fcpId;
  });
}

export function buildCategoryStats(assets: ProjectAssetRead[]): ReportCategoryStats {
  const counts = categoryCountsFromAssets(assets);
  const { greenPct, yellowPct, redPct } = categoryPercentages(counts);
  return {
    green: counts.green,
    yellow: counts.yellow,
    red: counts.red,
    pending: counts.pending,
    greenPct,
    yellowPct,
    redPct,
  };
}

export function buildPredictionStats(assets: ProjectAssetRead[]): ReportPredictionStat[] {
  const analyzed = assets.filter((a) => a.kind === 'image' && a.analysis);
  const total = analyzed.length;

  return PHOTO_REVIEW_CRITERIA.map((criterion) => {
    let pass = 0;
    for (const asset of analyzed) {
      if (asset.analysis && criterion.effective(asset.analysis)) {
        pass += 1;
      }
    }
    return {
      key: criterion.key,
      label: criterion.label,
      emoji: criterion.emoji,
      pass,
      total,
      pct: total === 0 ? 0 : Math.round((pass / total) * 100),
    };
  });
}

export function coverageForFcp(
  coverage: FcpCoverageRead | null,
  fcpId: string | null,
): ReportCoverageDetail {
  if (!coverage?.project.computed_at) return null;

  if (fcpId == null) {
    const p = coverage.project;
    return {
      coverageRatio: p.coverage_ratio,
      coveredCount: p.covered_count,
      compartmentCount: p.compartment_count,
    };
  }

  if (isUnassociatedFcpId(fcpId)) return null;

  const row = coverage.summaries.find((s) => s.fcp_id === fcpId);
  if (!row) return null;

  return {
    coverageRatio: row.coverage_ratio,
    coveredCount: row.covered_count,
    compartmentCount: row.compartment_count,
  };
}

export function pickCategorySampleAssets(
  assets: ProjectAssetRead[],
  assetFcpMap: Map<string, string>,
  fcpId?: string | null,
): Record<PhotoDocumentationCategory, ProjectAssetRead | null> {
  const scoped = filterScopeAssets(assets, assetFcpMap, fcpId);
  const analyzed = scoped
    .filter((a) => a.analysis)
    .sort((a, b) => b.created_at.localeCompare(a.created_at));

  const result: Record<PhotoDocumentationCategory, ProjectAssetRead | null> = {
    green: null,
    yellow: null,
    red: null,
  };

  for (const asset of analyzed) {
    const cat = analysisEffectiveCategory(asset.analysis);
    if (cat === 'green' || cat === 'yellow' || cat === 'red') {
      if (result[cat] == null) {
        result[cat] = asset;
      }
    }
  }

  return result;
}

export function formatCoveragePct(ratio: number): string {
  return `${Math.round(ratio * 100)}%`;
}
