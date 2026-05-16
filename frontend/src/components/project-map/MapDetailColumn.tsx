import type { ReactNode } from 'react';

export function MapDetailColumn({
  open,
  children,
}: {
  open: boolean;
  children: ReactNode;
}) {
  if (!open) return null;

  return (
    <aside className="flex w-full shrink-0 flex-col border-l border-slate-200 bg-white lg:w-96">
      <div className="flex max-h-[min(50vh,480px)] min-h-0 flex-1 flex-col overflow-hidden lg:max-h-none lg:min-h-[480px]">
        {children}
      </div>
    </aside>
  );
}
