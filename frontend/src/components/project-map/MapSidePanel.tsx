import type { ReactNode } from 'react';

export type SidePanelMode = 'hidden' | 'fcp' | 'photo';

export function MapSidePanel({
  mode,
  children,
}: {
  mode: SidePanelMode;
  children: ReactNode;
}) {
  const open = mode !== 'hidden';

  return (
    <div
      className={`pointer-events-none absolute inset-y-0 right-0 z-20 flex w-full max-w-md transition-transform duration-300 ease-out ${
        open ? 'translate-x-0' : 'translate-x-full'
      }`}
      aria-hidden={!open}
    >
      <div
        className={`pointer-events-auto m-3 flex max-h-[calc(100%-1.5rem)] w-[calc(100%-1.5rem)] flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl ${
          mode === 'hidden' ? 'invisible' : ''
        }`}
      >
        {children}
      </div>
    </div>
  );
}
