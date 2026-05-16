import type { PhotoAnalysisRead } from '../../api/client';
import { useDuplicateOverride } from './useDuplicateOverride';

export function DuplicateOverrideRow({
  projectId,
  assetId,
  analysis,
  onSaved,
  compact = false,
}: {
  projectId: string;
  assetId: string;
  analysis: PhotoAnalysisRead;
  onSaved: () => Promise<void>;
  compact?: boolean;
}) {
  const {
    saving,
    error,
    overridden,
    aiChipState,
    reviewerChipState,
    effectiveIsDuplicated,
    toggle,
  } = useDuplicateOverride({ projectId, assetId, analysis, onSaved });

  return (
    <div className="mb-3 border-b border-slate-100 pb-3">
      <p className={`font-semibold text-slate-900 ${compact ? 'text-xs' : 'text-sm'}`}>
        Duplicate
      </p>
      <p className={`mt-0.5 text-slate-500 ${compact ? 'text-[10px]' : 'text-xs'}`}>
        Detected: {analysis.is_duplicated ? 'Yes' : 'No'}
        {' · '}
        Effective: {effectiveIsDuplicated ? 'Yes' : 'No'}
      </p>
      <button
        type="button"
        disabled={saving}
        onClick={() => void toggle()}
        className={`mt-2 flex w-full items-center gap-2 rounded-lg border px-2 text-left transition-colors ${
          compact ? 'py-1.5' : 'py-2'
        } ${
          overridden
            ? 'border-violet-300 bg-violet-50/60 ring-1 ring-violet-300'
            : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
        } disabled:opacity-60`}
        title={
          overridden
            ? 'Click to reset and agree with AI'
            : 'Click to override duplicate detection'
        }
      >
        <span className={compact ? 'text-base' : 'text-lg'} aria-hidden>
          📋
        </span>
        <span
          className={`min-w-0 flex-1 font-medium text-slate-800 ${
            compact ? 'text-xs' : 'text-sm'
          }`}
        >
          Duplicate photo
        </span>
        <span
          className={`shrink-0 rounded-md border px-1.5 py-0.5 font-medium ${
            compact ? 'text-[10px]' : 'text-xs'
          } ${aiChipState.className}`}
        >
          AI: {aiChipState.label}
        </span>
        {overridden && (
          <span
            className={`shrink-0 rounded-md border px-1.5 py-0.5 font-medium ${
              compact ? 'text-[10px]' : 'text-xs'
            } ${reviewerChipState.className}`}
          >
            You: {reviewerChipState.label}
          </span>
        )}
      </button>
      {error && <p className="mt-1 text-xs text-red-700">{error}</p>}
    </div>
  );
}
