import { PHOTO_DOC_CATEGORIES } from '../project-images/photoDocumentationCategories';
import type { FcpPhotoRow } from './fcpPhotoTableUtils';

const warningCategory = PHOTO_DOC_CATEGORIES.find((c) => c.id === 'yellow');
const failedCategory = PHOTO_DOC_CATEGORIES.find((c) => c.id === 'red');

export function FcpSidePanel({
  projectName,
  rows,
  selectedFcpId,
  onSelectFcp,
  onClearFcpFilter,
}: {
  projectName: string;
  rows: FcpPhotoRow[];
  selectedFcpId: string | null;
  onSelectFcp: (fcpId: string | null) => void;
  onClearFcpFilter: () => void;
}) {
  const projectSelected = selectedFcpId === null;

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-slate-200 bg-white">
      <button
        type="button"
        onClick={onClearFcpFilter}
        className={`border-b border-slate-200 px-4 py-3 text-left transition hover:bg-slate-50 ${
          projectSelected ? 'bg-violet-50 ring-2 ring-inset ring-violet-500' : ''
        }`}
        aria-pressed={projectSelected}
        title="Show all FCPs"
      >
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Project
        </p>
        <p className="mt-0.5 truncate text-sm font-semibold text-slate-900">
          {projectName}
        </p>
      </button>

      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {rows.length === 0 ? (
          <p className="px-2 py-3 text-xs text-slate-500">
            Upload FCP polygons to see per-FCP breakdown.
          </p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {rows.map((row) => {
              const selected = selectedFcpId === row.fcpId;
              return (
                <li key={row.fcpId}>
                  <button
                    type="button"
                    onClick={() => onSelectFcp(selected ? null : row.fcpId)}
                    className={`w-full rounded-lg border border-slate-200 px-3 py-2.5 text-left transition hover:bg-slate-50 ${
                      selected ? 'bg-violet-50 ring-2 ring-inset ring-violet-500' : 'bg-white'
                    }`}
                    aria-pressed={selected}
                    title={row.fcpLabel}
                  >
                    <p className="truncate text-sm font-medium text-slate-900">
                      {row.fcpCode}
                    </p>
                    <div className="mt-2 flex gap-3 text-xs tabular-nums">
                      <span className="inline-flex items-center gap-1.5 text-slate-700">
                        <span
                          className="inline-block h-2 w-2 shrink-0 rounded-full"
                          style={{ backgroundColor: warningCategory?.color }}
                          aria-hidden
                        />
                        <span className="text-slate-500">Warning</span>
                        <span className="font-semibold">{row.yellow}</span>
                      </span>
                      <span className="inline-flex items-center gap-1.5 text-slate-700">
                        <span
                          className="inline-block h-2 w-2 shrink-0 rounded-full"
                          style={{ backgroundColor: failedCategory?.color }}
                          aria-hidden
                        />
                        <span className="text-slate-500">Failed</span>
                        <span className="font-semibold">{row.red}</span>
                      </span>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
}
