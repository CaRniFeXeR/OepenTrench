import { useCallback, useEffect, useId, useRef, useState } from 'react';

import {
  uploadProjectImageProjectsProjectIdImagesPost,
} from '../../api/client';
import {
  IMAGE_ACCEPT,
  MAX_IMAGE_BYTES,
  MAX_PHOTOS_PER_BATCH,
  isAllowedImageFile,
} from './constants';

const UPLOAD_CONCURRENCY = 4;

const WAIT_MESSAGES = [
  'Uploading takes a while — time for a short break.',
  'Still going — your trench map is being built in the background.',
  'Large batch detected — we are processing every photo.',
  'Almost there — good things take time.',
];

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function duplicateNamesInBatch(files: File[]): string[] {
  const counts = new Map<string, number>();
  for (const f of files) {
    counts.set(f.name, (counts.get(f.name) ?? 0) + 1);
  }
  return [...counts.entries()].filter(([, n]) => n > 1).map(([name]) => name);
}

type PhotoUploadZoneProps = {
  projectId: string;
  onRefresh: () => Promise<void>;
  onUploadingChange: (busy: boolean) => void;
};

type Phase = 'idle' | 'uploading' | 'summary';

type FileErrorRow = { name: string; reason: string };

export function PhotoUploadZone({
  projectId,
  onRefresh,
  onUploadingChange,
}: PhotoUploadZoneProps) {
  const inputId = useId();
  const folderInputId = `${inputId}-folder`;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const [phase, setPhase] = useState<Phase>('idle');
  const [dragOver, setDragOver] = useState(false);
  const [validationErrors, setValidationErrors] = useState<FileErrorRow[]>([]);
  const [duplicateNames, setDuplicateNames] = useState<string[]>([]);

  const [progressDone, setProgressDone] = useState(0);
  const [progressTotal, setProgressTotal] = useState(0);
  const [activeNames, setActiveNames] = useState<string[]>([]);
  const [batchStartMs, setBatchStartMs] = useState<number | null>(null);
  const [nowTick, setNowTick] = useState(() => Date.now());

  const [uploadFailures, setUploadFailures] = useState<FileErrorRow[]>([]);
  const [friendlyIndex, setFriendlyIndex] = useState(0);

  const [paused, setPaused] = useState(false);
  const pausedRef = useRef(false);
  const cancelledRef = useRef(false);
  const abortControllersRef = useRef(new Set<AbortController>());

  useEffect(() => {
    pausedRef.current = paused;
  }, [paused]);

  useEffect(() => {
    if (phase !== 'uploading') return;
    const id = window.setInterval(() => setNowTick(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [phase]);

  const etaRemainingMs =
    phase === 'uploading' &&
    batchStartMs !== null &&
    progressDone > 0 &&
    progressTotal > progressDone
      ? ((nowTick - batchStartMs) / progressDone) * (progressTotal - progressDone)
      : 0;

  const showFriendlyWait = phase === 'uploading' && etaRemainingMs > 60_000;

  useEffect(() => {
    if (!showFriendlyWait) return;
    const id = window.setInterval(
      () => setFriendlyIndex((i) => (i + 1) % WAIT_MESSAGES.length),
      17500,
    );
    return () => window.clearInterval(id);
  }, [showFriendlyWait]);

  const waitWhilePaused = async () => {
    while (pausedRef.current && !cancelledRef.current) {
      await sleep(120);
    }
  };

  const runUpload = useCallback(
    async (files: File[]) => {
      cancelledRef.current = false;
      abortControllersRef.current.clear();
      setPhase('uploading');
      onUploadingChange(true);
      setProgressTotal(files.length);
      setProgressDone(0);
      setBatchStartMs(Date.now());
      setActiveNames([]);
      setUploadFailures([]);
      setFriendlyIndex(0);

      const uploadOneFile = async (file: File) => {
        setActiveNames((prev) => [...prev, file.name]);
        try {
          if (cancelledRef.current) return;

          const ac = new AbortController();
          abortControllersRef.current.add(ac);
          let uploadError: unknown;
          try {
            const { error: errFromRes } = await uploadProjectImageProjectsProjectIdImagesPost({
              path: { project_id: projectId },
              body: { file: file as unknown as string, label: file.name },
              signal: ac.signal,
            });
            uploadError = errFromRes;
          } catch (err) {
            if (cancelledRef.current || ac.signal.aborted) return;
            uploadError = err;
          } finally {
            abortControllersRef.current.delete(ac);
          }

          if (cancelledRef.current) return;

          if (uploadError) {
            const detail =
              typeof uploadError === 'object' &&
              uploadError !== null &&
              'detail' in uploadError
                ? String((uploadError as { detail: unknown }).detail)
                : uploadError instanceof Error
                  ? uploadError.message
                  : 'Upload failed.';
            setUploadFailures((prev) => [...prev, { name: file.name, reason: detail }]);
          }
        } finally {
          setActiveNames((prev) => prev.filter((n) => n !== file.name));
          setProgressDone((n) => n + 1);
        }
      };

      let nextIndex = 0;

      const worker = async () => {
        while (!cancelledRef.current) {
          await waitWhilePaused();
          if (cancelledRef.current) break;

          const index = nextIndex;
          nextIndex += 1;
          if (index >= files.length) break;

          await uploadOneFile(files[index]);
        }
      };

      const workerCount = Math.min(UPLOAD_CONCURRENCY, files.length);
      await Promise.all(Array.from({ length: workerCount }, () => worker()));

      onUploadingChange(false);
      abortControllersRef.current.clear();
      await onRefresh();
      setPhase('summary');
      setActiveNames([]);
      setPaused(false);
      pausedRef.current = false;
    },
    [projectId, onRefresh, onUploadingChange],
  );

  const classifyAndSetFiles = useCallback(
    (raw: FileList | File[]) => {
      const list = Array.from(raw);
      const errors: FileErrorRow[] = [];
      const ok: File[] = [];

      if (list.length > MAX_PHOTOS_PER_BATCH) {
        setValidationErrors([
          {
            name: '—',
            reason: `Too many files (${list.length}). Maximum ${MAX_PHOTOS_PER_BATCH} per batch.`,
          },
        ]);
        setDuplicateNames([]);
        setPhase('idle');
        return;
      }

      for (const f of list) {
        if (!isAllowedImageFile(f)) {
          errors.push({
            name: f.name,
            reason: 'Not a supported image format (use JPG, PNG, WebP, or GIF).',
          });
          continue;
        }
        if (f.size > MAX_IMAGE_BYTES) {
          errors.push({
            name: f.name,
            reason: `Exceeds ${Math.round(MAX_IMAGE_BYTES / (1024 * 1024))} MB limit.`,
          });
          continue;
        }
        ok.push(f);
      }

      setValidationErrors(errors);
      setDuplicateNames(duplicateNamesInBatch(ok));

      if (ok.length > 0) {
        void runUpload(ok);
      } else {
        setPhase('idle');
      }
    },
    [runUpload],
  );

  const handlePauseToggle = () => {
    setPaused((p) => {
      const next = !p;
      pausedRef.current = next;
      return next;
    });
  };

  const handleCancel = () => {
    if (!window.confirm('Cancel upload? Files already uploaded will be kept.')) {
      return;
    }
    cancelledRef.current = true;
    for (const ac of abortControllersRef.current) {
      ac.abort();
    }
    abortControllersRef.current.clear();
    setPaused(false);
    pausedRef.current = false;
  };

  const handleReset = () => {
    setPhase('idle');
    setValidationErrors([]);
    setDuplicateNames([]);
    setProgressDone(0);
    setProgressTotal(0);
    setActiveNames([]);
    setUploadFailures([]);
    setBatchStartMs(null);
  };

  const pct =
    progressTotal > 0 ? Math.round((progressDone / progressTotal) * 100) : 0;

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">Photos</h3>
      <p className="mt-1 text-xs text-slate-500">
        Drag and drop photos or folders here, or click to browse. Uploads start
        automatically (up to {UPLOAD_CONCURRENCY} at a time). Formats: JPG,
        JPEG, PNG, WebP, GIF (HEIC is not supported yet). Max{' '}
        {MAX_PHOTOS_PER_BATCH} files per batch, {Math.round(MAX_IMAGE_BYTES / (1024 * 1024))}{' '}
        MB each.
      </p>

      {phase === 'idle' && (
        <div
          className={`mt-3 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-10 text-center transition ${
            dragOver
              ? 'border-slate-500 bg-slate-50'
              : 'border-slate-300 bg-slate-50/50 hover:border-slate-400'
          }`}
          role="button"
          tabIndex={0}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            if (e.dataTransfer.files?.length) {
              classifyAndSetFiles(e.dataTransfer.files);
            }
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            id={inputId}
            type="file"
            accept={IMAGE_ACCEPT}
            multiple
            className="hidden"
            onChange={(e) => {
              const fl = e.target.files;
              e.target.value = '';
              if (fl?.length) classifyAndSetFiles(fl);
            }}
          />
          <input
            ref={folderInputRef}
            id={folderInputId}
            type="file"
            multiple
            {...({ webkitdirectory: '', directory: '' } as React.InputHTMLAttributes<HTMLInputElement>)}
            className="hidden"
            onChange={(e) => {
              const fl = e.target.files;
              e.target.value = '';
              if (fl?.length) classifyAndSetFiles(fl);
            }}
          />
          <span className="text-sm font-medium text-slate-700">
            Drag and drop photos or folders, or click to browse
          </span>
          <span className="mt-2 text-xs text-slate-500">
            Or pick a folder:{' '}
            <button
              type="button"
              className="font-medium text-slate-800 underline decoration-slate-400 hover:decoration-slate-800"
              onClick={(e) => {
                e.stopPropagation();
                folderInputRef.current?.click();
              }}
            >
              Choose folder
            </button>
          </span>
        </div>
      )}

      {validationErrors.length > 0 && (
        <ul className="mt-3 max-h-32 space-y-1 overflow-y-auto text-xs text-red-700">
          {validationErrors.map((row) => (
            <li key={`${row.name}-${row.reason}`}>
              <span className="font-medium">{row.name}:</span> {row.reason}
            </li>
          ))}
        </ul>
      )}

      {(phase === 'uploading' || phase === 'summary') && duplicateNames.length > 0 && (
        <p className="mt-2 text-xs text-amber-800">
          Duplicate file names in this batch: {duplicateNames.join(', ')}
        </p>
      )}

      {phase === 'uploading' && (
        <div className="mt-4 space-y-3">
          <div>
            <div className="flex justify-between text-xs text-slate-600">
              <span>
                {progressDone} / {progressTotal} — {pct}%
              </span>
              {etaRemainingMs > 0 && (
                <span>
                  ~
                  {Math.max(1, Math.ceil(etaRemainingMs / 60000))} min remaining
                </span>
              )}
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-full bg-slate-800 transition-all duration-300"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
          {activeNames.length > 0 && (
            <p className="text-xs text-slate-600">
              Uploading ({activeNames.length} active):{' '}
              <span className="font-mono">{activeNames.join(', ')}</span>
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-50"
              onClick={handlePauseToggle}
            >
              {paused ? 'Resume' : 'Pause'}
            </button>
            <button
              type="button"
              className="rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-800 hover:bg-red-100"
              onClick={handleCancel}
            >
              Cancel
            </button>
          </div>
          {showFriendlyWait && (
            <p
              className="text-xs text-slate-600 transition-opacity duration-500"
              key={friendlyIndex}
            >
              {WAIT_MESSAGES[friendlyIndex]}
            </p>
          )}
        </div>
      )}

      {phase === 'summary' && (
        <div className="mt-4 space-y-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-3">
          <p className="text-sm font-semibold text-slate-900">Upload summary</p>
          <p className="text-xs text-slate-600">
            Finished: {progressDone} of {progressTotal} in this run. Successful
            uploads: {progressDone - uploadFailures.length}.
          </p>
          {uploadFailures.length > 0 && (
            <ul className="max-h-24 space-y-1 overflow-y-auto text-xs text-red-700">
              {uploadFailures.map((f) => (
                <li key={f.name}>
                  <span className="font-medium">{f.name}:</span> {f.reason}
                </li>
              ))}
            </ul>
          )}
          <button
            type="button"
            className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800"
            onClick={handleReset}
          >
            Upload more photos
          </button>
        </div>
      )}
    </section>
  );
}
