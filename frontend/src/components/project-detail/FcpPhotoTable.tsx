import type { FcpPhotoRow } from './fcpPhotoTableUtils';
import { CATEGORY_COLORS } from '../project-map/photoMarkerPaint';

const COLUMN_HEADERS: {
  key: 'green' | 'yellow' | 'red';
  label: string;
}[] = [
  { key: 'green', label: 'Good' },
  { key: 'yellow', label: 'Warning' },
  { key: 'red', label: 'Failed' },
];

export function FcpPhotoTable({
  rows,
  selectedFcpId,
  onSelectFcp,
}: {
  rows: FcpPhotoRow[];
  selectedFcpId: string | null;
  onSelectFcp: (fcpId: string | null) => void;
}) {
  if (rows.length === 0) {
    return (
      <p className="mt-4 text-xs text-slate-500">
        Upload FCP polygons to see per-FCP breakdown.
      </p>
    );
  }

  return (
    <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
      <table className="w-full min-w-[280px] text-left text-sm">
        <thead>
          <tr className="border-b border-slate-100 bg-slate-50 text-xs font-medium uppercase tracking-wide text-slate-500">
            <th className="px-3 py-2" scope="col">
              FCP
            </th>
            {COLUMN_HEADERS.map((col) => (
              <th key={col.key} className="px-3 py-2 text-right tabular-nums" scope="col">
                <span className="inline-flex items-center justify-end gap-1.5">
                  <span
                    className="inline-block h-2 w-2 shrink-0 rounded-full"
                    style={{ backgroundColor: CATEGORY_COLORS[col.key] }}
                    aria-hidden
                  />
                  <span className="sr-only">{col.label}</span>
                  <span className="hidden sm:inline">{col.label}</span>
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row) => {
            const selected = selectedFcpId === row.fcpId;
            return (
              <tr key={row.fcpId}>
                <td colSpan={4} className="p-0">
                  <button
                    type="button"
                    onClick={() => onSelectFcp(selected ? null : row.fcpId)}
                    className={`flex w-full items-center text-left transition hover:bg-slate-50 ${
                      selected ? 'bg-violet-50 ring-2 ring-inset ring-violet-500' : ''
                    }`}
                    aria-pressed={selected}
                    title={row.fcpLabel}
                  >
                    <span className="min-w-0 flex-1 truncate px-3 py-2 font-medium text-slate-900">
                      {row.fcpCode}
                    </span>
                    <span className="w-12 px-3 py-2 text-right tabular-nums text-slate-700">
                      {row.green}
                    </span>
                    <span className="w-12 px-3 py-2 text-right tabular-nums text-slate-700">
                      {row.yellow}
                    </span>
                    <span className="w-12 px-3 py-2 text-right tabular-nums text-slate-700">
                      {row.red}
                    </span>
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
