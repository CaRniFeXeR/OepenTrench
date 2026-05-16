import type { FcpCoverageSummaryRead, MapPhotoMarkerRead } from '../../api/client';
import { PHOTO_DOC_CATEGORIES } from '../project-images/photoDocumentationCategories';
import {
  categoryPercentages,
  DocumentationStatusBar,
} from '../ui/DocumentationStatusBar';
import { categoryCounts } from './mapPhotoUtils';

export function MapOverlayPanels({
  projectName,
  fcpCount,
  photos,
  selectedFcpId = null,
  coverageSummary = null,
  coverageLoading = false,
}: {
  projectName: string;
  fcpCount: number;
  photos: MapPhotoMarkerRead[];
  selectedFcpId?: string | null;
  coverageSummary?: FcpCoverageSummaryRead | null;
  coverageLoading?: boolean;
}) {
  const counts = categoryCounts(photos);
  const { greenPct, yellowPct, redPct } = categoryPercentages(counts);
  const pctByCategory = { green: greenPct, yellow: yellowPct, red: redPct };
  const fcpView = selectedFcpId != null;

  return (
    <>
      <div className="pointer-events-none absolute bottom-3 left-3 right-3 z-10 flex flex-wrap items-end justify-between gap-3">
        <div className="rounded-lg border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-md backdrop-blur-sm">
          <p className="font-medium text-slate-900">
            {projectName} · {fcpCount} FCPs · {photos.length} GPS photos
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white/95 px-3 py-2 shadow-md backdrop-blur-sm">
          <p className="mb-1 text-xs font-medium text-slate-700">Photo documentation</p>
          <DocumentationStatusBar
            greenPct={greenPct}
            yellowPct={yellowPct}
            redPct={redPct}
            widthClassName="w-48"
          />
        </div>
      </div>

      <div className="pointer-events-none absolute right-3 top-3 z-10 w-40 rounded-lg border border-slate-200 bg-white/95 p-3 text-xs shadow-md backdrop-blur-sm">
        {fcpView ? (
          <TrenchCoveragePanel
            summary={coverageSummary}
            loading={coverageLoading}
          />
        ) : (
          <>
            <p className="mb-2 font-semibold text-slate-900">Photo status</p>
            {PHOTO_DOC_CATEGORIES.map((cat) => (
              <StatusRow
                key={cat.id}
                label={cat.label}
                pct={pctByCategory[cat.id]}
                color={cat.color}
              />
            ))}
          </>
        )}
      </div>
    </>
  );
}

function TrenchCoveragePanel({
  summary,
  loading,
}: {
  summary: FcpCoverageSummaryRead | null;
  loading: boolean;
}) {
  if (loading) {
    return (
      <>
        <p className="mb-2 font-semibold text-slate-900">Trench coverage</p>
        <p className="text-slate-500">Calculating…</p>
      </>
    );
  }

  if (!summary || summary.compartment_count === 0) {
    return (
      <>
        <p className="mb-2 font-semibold text-slate-900">Trench coverage</p>
        <p className="text-2xl font-semibold text-slate-800">—</p>
        <p className="mt-1 text-slate-500">No segments</p>
      </>
    );
  }

  const pct = Math.round(summary.coverage_ratio * 100);
  const segmentLabel =
    summary.compartment_count === 1 ? 'segment' : 'segments';

  return (
    <>
      <p className="mb-2 font-semibold text-slate-900">Trench coverage</p>
      <p className="text-2xl font-semibold text-slate-800">{pct}%</p>
      <p className="mt-1 text-slate-600">
        {summary.covered_count}/{summary.compartment_count} {segmentLabel} covered
      </p>
    </>
  );
}

function StatusRow({
  label,
  pct,
  color,
}: {
  label: string;
  pct: number;
  color: string;
}) {
  return (
    <div className="mb-1.5 flex items-center justify-between gap-2">
      <span className="flex items-center gap-1.5 text-slate-600">
        <span
          className="inline-block h-2 w-2 rounded-sm"
          style={{ backgroundColor: color }}
        />
        {label}
      </span>
      <span className="font-medium text-slate-800">{pct}%</span>
    </div>
  );
}
