import { useMemo } from 'react';
import type { FeatureCollection } from 'geojson';

import type { FcpCoverageRead, MapPhotoMarkerRead, ProjectDetailRead } from '../../../api/client';
import { TrenchCoverageSection } from '../TrenchCoverageSection';
import {
  assetIdToFcpId,
  buildFcpPhotoRows,
  buildUnassociatedPhotoRow,
  UNASSOCIATED_FCP_ID,
} from '../fcpPhotoTableUtils';
import { ReportCoverageTable } from './ReportCoverageTable';
import { ReportFcpSection } from './ReportFcpSection';
import { ReportStatsBlock } from './ReportStatsBlock';
import {
  buildCategoryStats,
  buildPredictionStats,
  coverageForFcp,
} from './reportStatsUtils';

export function ProjectReportTab({
  project,
  mapData,
  mapPhotos,
  coverage,
  coverageLoading,
}: {
  project: ProjectDetailRead;
  mapData: FeatureCollection | null;
  mapPhotos: MapPhotoMarkerRead[];
  coverage: FcpCoverageRead | null;
  coverageLoading: boolean;
}) {
  const assetFcpMap = useMemo(() => assetIdToFcpId(mapPhotos), [mapPhotos]);
  const fcpRows = useMemo(
    () => buildFcpPhotoRows({ assets: project.assets, mapPhotos, mapData }),
    [project.assets, mapPhotos, mapData],
  );
  const unassociatedRow = useMemo(
    () => buildUnassociatedPhotoRow(project.assets, assetFcpMap),
    [project.assets, assetFcpMap],
  );

  const projectCategoryStats = useMemo(
    () => buildCategoryStats(project.assets),
    [project.assets],
  );
  const projectPredictionStats = useMemo(
    () => buildPredictionStats(project.assets),
    [project.assets],
  );
  const projectCoverage = useMemo(() => coverageForFcp(coverage, null), [coverage]);

  const sortedFcpRows = useMemo(
    () =>
      [...fcpRows].sort((a, b) =>
        a.fcpCode.localeCompare(b.fcpCode, undefined, { sensitivity: 'base' }),
      ),
    [fcpRows],
  );

  return (
    <section
      id="project-report-print"
      className="flex min-h-0 flex-1 flex-col overflow-hidden bg-slate-50 print:h-auto print:max-h-none print:overflow-visible print:bg-white"
    >
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4 print:overflow-visible sm:px-6">
        <header className="mb-6 print:break-after-avoid">
          <h2 className="text-lg font-semibold text-slate-900">Project report</h2>
          <p className="mt-1 text-sm text-slate-600">
            Documentation quality, analysis checks
            <span className="print:hidden">, and trench coverage</span> for{' '}
            {project.name}.
          </p>
        </header>

        <section className="mb-8 rounded-xl border border-slate-200 bg-white p-4 shadow-sm print:mb-6 print:break-after-avoid print:shadow-none">
          <h3 className="text-base font-semibold text-slate-900">Project overview</h3>
          <div className="mt-4">
            <ReportStatsBlock
              categoryStats={projectCategoryStats}
              predictionStats={projectPredictionStats}
              coverage={projectCoverage}
            />
          </div>
        </section>

        {sortedFcpRows.length > 0 || unassociatedRow ? (
          <div className="mb-8 space-y-6 print:mb-6">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Per FCP
            </h3>
            {sortedFcpRows.map((row) => (
              <ReportFcpSection
                key={row.fcpId}
                projectId={project.id}
                title={row.fcpCode}
                subtitle={row.fcpLabel !== row.fcpCode ? row.fcpLabel : undefined}
                assets={project.assets}
                assetFcpMap={assetFcpMap}
                fcpId={row.fcpId}
                coverage={coverage}
              />
            ))}
            {unassociatedRow && (
              <ReportFcpSection
                projectId={project.id}
                title={unassociatedRow.fcpCode}
                subtitle={unassociatedRow.fcpLabel}
                assets={project.assets}
                assetFcpMap={assetFcpMap}
                fcpId={UNASSOCIATED_FCP_ID}
                coverage={coverage}
              />
            )}
          </div>
        ) : (
          <p className="mb-8 text-sm text-slate-500 print:mb-6">
            Upload FCP polygons to see per-FCP breakdown.
          </p>
        )}

        <ReportCoverageTable
          fcpRows={fcpRows}
          unassociatedRow={unassociatedRow}
          coverage={coverage}
          coverageLoading={coverageLoading}
        />

        <TrenchCoverageSection
          embedded
          className="mt-8 print:hidden print:shadow-none"
          coverage={coverage}
          loading={coverageLoading}
        />
      </div>
    </section>
  );
}
