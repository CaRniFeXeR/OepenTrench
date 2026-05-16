import { useEffect, useMemo, useState } from 'react';

import type { ProjectAssetRead } from '../../api/client';
import { projectImageContentUrl } from '../project-map/imageContentUrl';
import { AnalysisTagRow, qualityBadge } from './analysisDisplay';
import {
  filterImages,
  formatAssetDate,
  imageAssets,
  paginateImages,
  sortImages,
  type ImageSortOption,
  type PageSize,
  type QualityFilter,
} from './projectImageListUtils';

export function ProjectImagesPanel({
  projectId,
  assets,
}: {
  projectId: string;
  assets: ProjectAssetRead[];
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [qualityFilter, setQualityFilter] = useState<QualityFilter>('all');
  const [sort, setSort] = useState<ImageSortOption>('newest');
  const [pageSize, setPageSize] = useState<PageSize>(25);
  const [page, setPage] = useState(1);

  const allImages = useMemo(() => imageAssets(assets), [assets]);

  const filteredSorted = useMemo(
    () => sortImages(filterImages(allImages, qualityFilter, searchQuery), sort),
    [allImages, qualityFilter, searchQuery, sort],
  );

  const { pageItems, totalPages, startIndex, endIndex } = useMemo(
    () => paginateImages(filteredSorted, page, pageSize),
    [filteredSorted, page, pageSize],
  );

  useEffect(() => {
    setPage(1);
  }, [searchQuery, qualityFilter, sort, pageSize]);

  return (
    <section className="mt-8 rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-4 sm:px-6">
        <h2 className="text-lg font-semibold text-slate-900">Project images</h2>
        <p className="mt-1 text-sm text-slate-600">
          {allImages.length === 0
            ? 'No photos uploaded yet.'
            : `${allImages.length} photo${allImages.length === 1 ? '' : 's'} on server`}
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <span className="whitespace-nowrap">Search</span>
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by filename"
              className="min-w-[12rem] rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            />
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <span className="whitespace-nowrap">Quality</span>
            <select
              value={qualityFilter}
              onChange={(e) => setQualityFilter(e.target.value as QualityFilter)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            >
              <option value="all">All</option>
              <option value="good">Good</option>
              <option value="poor">Poor</option>
              <option value="missing">Missing</option>
              <option value="pending">Pending analysis</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <span className="whitespace-nowrap">Sort</span>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as ImageSortOption)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            >
              <option value="newest">Newest first</option>
              <option value="name_asc">Filename A–Z</option>
              <option value="name_desc">Filename Z–A</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <span className="whitespace-nowrap">Per page</span>
            <select
              value={pageSize}
              onChange={(e) => setPageSize(Number(e.target.value) as PageSize)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
        </div>
      </div>

      {allImages.length === 0 ? (
        <p className="px-6 py-8 text-center text-sm text-slate-500">
          Upload photos above to see them listed here with analysis results.
        </p>
      ) : filteredSorted.length === 0 ? (
        <p className="px-6 py-8 text-center text-sm text-slate-500">
          No photos match your filters.
        </p>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50 text-xs font-medium uppercase tracking-wide text-slate-500">
                  <th className="px-4 py-3 sm:px-6" scope="col">
                    Preview
                  </th>
                  <th className="px-4 py-3" scope="col">
                    Filename
                  </th>
                  <th className="px-4 py-3" scope="col">
                    Uploaded
                  </th>
                  <th className="px-4 py-3" scope="col">
                    Quality
                  </th>
                  <th className="px-4 py-3 sm:pr-6" scope="col">
                    Analysis
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pageItems.map((asset) => {
                  const badge = qualityBadge(asset.analysis, { pendingWhenNull: true });
                  return (
                    <tr key={asset.id} className="align-top hover:bg-slate-50/80">
                      <td className="px-4 py-3 sm:px-6">
                        <img
                          src={projectImageContentUrl(projectId, asset.id)}
                          alt=""
                          className="h-12 w-12 rounded-md border border-slate-200 object-cover bg-slate-100"
                        />
                      </td>
                      <td className="max-w-[12rem] px-4 py-3 font-medium text-slate-900">
                        <span className="line-clamp-2 break-all" title={asset.original_label}>
                          {asset.original_label}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                        {formatAssetDate(asset.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${badge.className}`}
                        >
                          {badge.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 sm:pr-6">
                        {asset.analysis ? (
                          <AnalysisTagRow analysis={asset.analysis} compact />
                        ) : (
                          <span className="text-xs text-slate-500">Analysis pending</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <footer className="flex flex-col gap-3 border-t border-slate-100 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <p className="text-sm text-slate-600">
              {filteredSorted.length === 0
                ? 'No results'
                : `Showing ${startIndex + 1}–${endIndex} of ${filteredSorted.length}`}
              {filteredSorted.length !== allImages.length &&
                ` (filtered from ${allImages.length})`}
            </p>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
              >
                Previous
              </button>
              <span className="text-sm text-slate-600">
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
              >
                Next
              </button>
            </div>
          </footer>
        </>
      )}
    </section>
  );
}
