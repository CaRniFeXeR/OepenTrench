import { useCallback, useId, useRef, useState } from 'react';
import type { FeatureCollection } from 'geojson';

import {
  uploadProjectGeojsonProjectsProjectIdGeojsonPost,
} from '../../api/client';
import {
  MAX_GEOJSON_BYTES,
  GEOJSON_ACCEPT,
  isAllowedGeoJsonFile,
} from './constants';
import {
  normalizeFeatureCollection,
  stripBlankFillColors,
} from '../../normalizeExampleGeojson';

type GeoJsonUploadZoneProps = {
  projectId: string;
  hasGeoJsonAsset: boolean;
  onRefresh: () => Promise<void>;
  onMapData: (data: FeatureCollection) => void;
  onUploadingChange: (busy: boolean) => void;
};

export function GeoJsonUploadZone({
  projectId,
  hasGeoJsonAsset,
  onRefresh,
  onMapData,
  onUploadingChange,
}: GeoJsonUploadZoneProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successHint, setSuccessHint] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const applyFile = useCallback(
    async (file: File) => {
      setError(null);
      setSuccessHint(null);

      if (!isAllowedGeoJsonFile(file)) {
        setError('Use a .geojson or .json file.');
        return;
      }
      if (file.size > MAX_GEOJSON_BYTES) {
        setError(
          `File is too large (max ${Math.round(MAX_GEOJSON_BYTES / (1024 * 1024))} MB).`,
        );
        return;
      }

      let parsedFc: FeatureCollection;
      try {
        const text = await file.text();
        const json: unknown = JSON.parse(text);
        parsedFc = stripBlankFillColors(normalizeFeatureCollection(json));
      } catch {
        setError('Could not read valid GeoJSON from this file.');
        return;
      }

      const segmentCount = parsedFc.features.length;

      setUploading(true);
      onUploadingChange(true);
      const { data, error: apiError } =
        await uploadProjectGeojsonProjectsProjectIdGeojsonPost({
          path: { project_id: projectId },
          body: { file: file as unknown as string, label: file.name },
        });
      setUploading(false);
      onUploadingChange(false);

      if (apiError || !data) {
        const detail =
          apiError && typeof apiError === 'object' && 'detail' in apiError
            ? String((apiError as { detail: unknown }).detail)
            : 'Upload failed.';
        setError(detail);
        return;
      }

      onMapData(parsedFc);
      setSuccessHint(
        `Route file loaded — ${segmentCount} feature${segmentCount === 1 ? '' : 's'} detected.`,
      );
      await onRefresh();
    },
    [projectId, onRefresh, onMapData, onUploadingChange],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) void applyFile(f);
    },
    [applyFile],
  );

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">GeoJSON route</h3>
      <p className="mt-1 text-xs text-slate-500">
        One route file (.geojson / .json), max{' '}
        {Math.round(MAX_GEOJSON_BYTES / (1024 * 1024))} MB. Validated on the
        server.
      </p>

      {!hasGeoJsonAsset && (
        <div
          className="mt-3 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-950"
          role="status"
        >
          <strong className="font-medium">GeoJSON route file is missing.</strong>{' '}
          The map view cannot be generated until this file is added. You can
          upload it now or return to this project later.
        </div>
      )}

      <div
        role="button"
        tabIndex={0}
        className={`mt-3 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 text-center transition ${
          dragOver
            ? 'border-slate-500 bg-slate-50'
            : 'border-slate-300 bg-slate-50/50 hover:border-slate-400'
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept={GEOJSON_ACCEPT}
          className="hidden"
          disabled={uploading}
          onChange={(e) => {
            const f = e.target.files?.[0];
            e.target.value = '';
            if (f) void applyFile(f);
          }}
        />
        <span className="text-sm font-medium text-slate-700">
          Drop GeoJSON here or click to browse
        </span>
        <span className="mt-1 text-xs text-slate-500">
          {uploading ? 'Uploading…' : 'One file per upload'}
        </span>
      </div>

      {error && (
        <p className="mt-2 text-xs text-red-600" role="alert">
          {error}
        </p>
      )}
      {successHint && (
        <p className="mt-2 text-xs font-medium text-emerald-700" role="status">
          {successHint}
        </p>
      )}
    </section>
  );
}
