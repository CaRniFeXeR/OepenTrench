import { useMemo } from 'react';

import { PHOTO_DOC_CATEGORIES } from '../project-images/photoDocumentationCategories';
import { UNASSOCIATED_FCP_ID, type FcpPhotoRow } from './fcpPhotoTableUtils';

const warningCategory = PHOTO_DOC_CATEGORIES.find((c) => c.id === 'yellow');
const failedCategory = PHOTO_DOC_CATEGORIES.find((c) => c.id === 'red');

function FcpPhotoRowButton({
  row,
  selected,
  onSelect,
}: {
  row: FcpPhotoRow;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-lg border border-slate-200 px-3 py-2.5 text-left transition hover:bg-slate-50 ${
        selected ? 'bg-violet-50 ring-2 ring-inset ring-violet-500' : 'bg-white'
      }`}
      aria-pressed={selected}
      title={row.fcpLabel}
    >
      <p className="truncate text-sm font-medium text-slate-900">{row.fcpCode}</p>
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
  );
}

export function FcpSidePanel({
  projectName,
  rows,
  unassociatedRow,
  selectedFcpId,
  onSelectFcp,
  onClearFcpFilter,
}: {
  projectName: string;
  rows: FcpPhotoRow[];
  unassociatedRow?: FcpPhotoRow | null;
  selectedFcpId: string | null;
  onSelectFcp: (fcpId: string | null) => void;
  onClearFcpFilter: () => void;
}) {
  const projectSelected = selectedFcpId === null;
  const sortedRows = useMemo(
    () =>
      [...rows].sort((a, b) => {
        const problematicDiff = b.yellow + b.red - (a.yellow + a.red);
        if (problematicDiff !== 0) return problematicDiff;
        return a.fcpCode.localeCompare(b.fcpCode, undefined, { sensitivity: 'base' });
      }),
    [rows],
  );

  const hasFcpRows = sortedRows.length > 0;
  const hasUnassociated = unassociatedRow != null;

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
        {!hasFcpRows && !hasUnassociated ? (
          <p className="px-2 py-3 text-xs text-slate-500">
            Upload FCP polygons to see per-FCP breakdown.
          </p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {hasUnassociated && unassociatedRow && (
              <li>
                <FcpPhotoRowButton
                  row={unassociatedRow}
                  selected={selectedFcpId === UNASSOCIATED_FCP_ID}
                  onSelect={() =>
                    onSelectFcp(
                      selectedFcpId === UNASSOCIATED_FCP_ID ? null : UNASSOCIATED_FCP_ID,
                    )
                  }
                />
              </li>
            )}
            {sortedRows.map((row) => (
              <li key={row.fcpId}>
                <FcpPhotoRowButton
                  row={row}
                  selected={selectedFcpId === row.fcpId}
                  onSelect={() => onSelectFcp(selectedFcpId === row.fcpId ? null : row.fcpId)}
                />
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
