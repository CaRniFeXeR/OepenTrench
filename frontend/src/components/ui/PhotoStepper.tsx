export function PhotoStepper({
  photoIndex,
  photoTotal,
  contextLabel,
  onPrev,
  onNext,
  disabled = false,
  variant = 'default',
}: {
  photoIndex: number;
  photoTotal: number;
  contextLabel?: string;
  onPrev: () => void;
  onNext: () => void;
  disabled?: boolean;
  variant?: 'default' | 'compact' | 'footer';
}) {
  const indexLabel =
    photoIndex >= 0 && photoTotal > 0
      ? `Photo ${photoIndex + 1} of ${photoTotal}${contextLabel ? ` in ${contextLabel}` : ''}`
      : `${photoTotal} photos`;

  if (variant === 'compact') {
    return (
      <div className="flex items-center justify-between gap-2 border-t border-slate-100 pt-4">
        <button
          type="button"
          disabled={disabled || photoTotal === 0}
          onClick={onPrev}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-40"
          aria-label="Previous photo"
        >
          ←
        </button>
        <span className="text-xs text-slate-600">{indexLabel}</span>
        <button
          type="button"
          disabled={disabled || photoTotal === 0}
          onClick={onNext}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-40"
          aria-label="Next photo"
        >
          →
        </button>
      </div>
    );
  }

  if (variant === 'footer') {
    return (
      <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-600">
        <button
          type="button"
          onClick={onPrev}
          disabled={disabled || photoTotal === 0}
          className="font-medium text-violet-700 hover:underline disabled:opacity-40"
        >
          ← Previous photo
        </button>
        <span>{indexLabel}</span>
        <button
          type="button"
          onClick={onNext}
          disabled={disabled || photoTotal === 0}
          className="font-medium text-violet-700 hover:underline disabled:opacity-40"
        >
          Next photo →
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between gap-2 border-t border-slate-100 pt-4">
      <button
        type="button"
        disabled={disabled || photoTotal === 0}
        onClick={onPrev}
        className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-40"
        aria-label="Previous photo"
      >
        ←
      </button>
      <span className="text-xs text-slate-600">{indexLabel}</span>
      <button
        type="button"
        disabled={disabled || photoTotal === 0}
        onClick={onNext}
        className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-40"
        aria-label="Next photo"
      >
        →
      </button>
    </div>
  );
}
