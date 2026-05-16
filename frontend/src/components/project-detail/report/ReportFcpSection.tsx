import type { FcpCoverageRead, ProjectAssetRead } from '../../../api/client';
import { CategorySampleStrip } from './CategorySampleStrip';
import { ReportStatsBlock } from './ReportStatsBlock';
import {
  buildCategoryStats,
  buildPredictionStats,
  coverageForFcp,
  filterScopeAssets,
  pickCategorySampleAssets,
} from './reportStatsUtils';

export function ReportFcpSection({
  projectId,
  title,
  subtitle,
  assets,
  assetFcpMap,
  fcpId,
  coverage,
}: {
  projectId: string;
  title: string;
  subtitle?: string;
  assets: ProjectAssetRead[];
  assetFcpMap: Map<string, string>;
  fcpId: string | null;
  coverage: FcpCoverageRead | null;
}) {
  const scopedAssets = filterScopeAssets(assets, assetFcpMap, fcpId);
  const categoryStats = buildCategoryStats(scopedAssets);
  const predictionStats = buildPredictionStats(scopedAssets);
  const coverageDetail = coverageForFcp(coverage, fcpId);
  const samples = pickCategorySampleAssets(assets, assetFcpMap, fcpId);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm print:break-inside-avoid print:shadow-none print:border-slate-300">
      <header className="border-b border-slate-100 pb-3">
        <h3 className="text-base font-semibold text-slate-900">{title}</h3>
        {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
      </header>
      <div className="pt-4">
        <ReportStatsBlock
          categoryStats={categoryStats}
          predictionStats={predictionStats}
          coverage={coverageDetail}
        />
        <CategorySampleStrip projectId={projectId} samples={samples} />
      </div>
    </section>
  );
}
