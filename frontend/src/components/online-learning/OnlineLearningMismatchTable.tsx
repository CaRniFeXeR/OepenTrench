import { Link } from 'react-router-dom';

import type { OnlineLearningMismatchItemRead } from '../../api/client';
import { formatAssetDate } from '../project-images/projectImageListUtils';
import { photoDocCategoryLabel } from '../project-images/photoDocumentationCategories';
import { projectImageContentUrl } from '../project-map/imageContentUrl';
import { mismatchFieldLabel } from './onlineLearningLabels';
import type { OnlineLearningPageSize } from './useOnlineLearningDisagreements';

function categoryLabel(cat: string | null | undefined): string {
  if (cat === 'green' || cat === 'yellow' || cat === 'red') {
    return photoDocCategoryLabel(cat);
  }
  return '—';
}

export function OnlineLearningMismatchTable({
  items,
  total,
  loading,
  page,
  pageSize,
  totalPages,
  startIndex,
  endIndex,
  onPageChange,
  onPageSizeChange,
}: {
  items: OnlineLearningMismatchItemRead[];
  total: number;
  loading: boolean;
  page: number;
  pageSize: OnlineLearningPageSize;
  totalPages: number;
  startIndex: number;
  endIndex: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: OnlineLearningPageSize) => void;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-4 sm:px-6">
        <h2 className="text-lg font-semibold text-slate-900">Disagreement photos</h2>
        <p className="mt-1 text-sm text-slate-600">
          Reviewed photos where the reviewer label differs from the AI prediction.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <span className="whitespace-nowrap">Per page</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value) as OnlineLearningPageSize)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
        </div>
      </div>

      {loading && items.length === 0 ? (
        <p className="px-6 py-8 text-center text-sm text-slate-500">Loading…</p>
      ) : total === 0 ? (
        <p className="px-6 py-8 text-center text-sm text-slate-500">
          No reviewed photos with AI vs reviewer disagreement yet.
        </p>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50 text-xs font-medium uppercase tracking-wide text-slate-500">
                  <th className="px-4 py-3 sm:px-6" scope="col">
                    Preview
                  </th>
                  <th className="px-4 py-3" scope="col">
                    Project
                  </th>
                  <th className="px-4 py-3" scope="col">
                    Filename
                  </th>
                  <th className="px-4 py-3" scope="col">
                    AI category
                  </th>
                  <th className="px-4 py-3" scope="col">
                    Reviewer category
                  </th>
                  <th className="px-4 py-3 sm:pr-6" scope="col">
                    Mismatch
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={item.asset_id} className="align-top hover:bg-slate-50/80">
                    <td className="px-4 py-3 sm:px-6">
                      <img
                        src={projectImageContentUrl(item.project_id, item.asset_id)}
                        alt=""
                        className="h-12 w-12 rounded-md border border-slate-200 bg-slate-100 object-cover"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/projects/${item.project_id}`}
                        className="font-medium text-slate-900 hover:text-slate-600 hover:underline"
                      >
                        {item.project_name}
                      </Link>
                      <p className="mt-0.5 text-xs text-slate-500">
                        Reviewed {formatAssetDate(item.reviewed_at)}
                      </p>
                    </td>
                    <td className="max-w-[12rem] px-4 py-3 font-medium text-slate-900">
                      <span className="line-clamp-2 break-all" title={item.original_label}>
                        {item.original_label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-700">
                      {categoryLabel(item.analysis.category)}
                    </td>
                    <td className="px-4 py-3 text-slate-700">
                      {categoryLabel(item.analysis.effective_category)}
                    </td>
                    <td className="px-4 py-3 sm:pr-6">
                      <div className="flex flex-wrap gap-1">
                        {item.mismatch_fields.map((field) => (
                          <span
                            key={field}
                            className="inline-flex rounded-full bg-violet-100 px-2 py-0.5 text-xs font-medium text-violet-800"
                          >
                            {mismatchFieldLabel(field)}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <footer className="flex flex-col gap-3 border-t border-slate-100 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <p className="text-sm text-slate-600">
              {total === 0 ? 'No results' : `Showing ${startIndex}–${endIndex} of ${total}`}
            </p>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={page <= 1 || loading}
                onClick={() => onPageChange(Math.max(1, page - 1))}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
              >
                Previous
              </button>
              <span className="text-sm text-slate-600">
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages || loading}
                onClick={() => onPageChange(Math.min(totalPages, page + 1))}
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
