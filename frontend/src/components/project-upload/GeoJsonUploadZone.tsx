import { useCallback, useId, useRef, useState } from 'react';
import type { FeatureCollection } from 'geojson';

import type { ProjectAssetRead } from '../../api/client';
import { uploadProjectGeojsonProjectsProjectIdGeojsonPost } from '../../api/client';
import {
  MAX_GEOJSON_BYTES,
  GEOJSON_ACCEPT,
  TRENCHES_GEOJSON_SUFFIX,
  FCP_POLYGONS_GEOJSON_SUFFIX,
  geojsonChecklistFromAssets,
  isAllowedGeoJsonFile,
  requiredGeojsonSuffixForFile,
} from './constants';
import {
  normalizeFeatureCollection,
  stripBlankFillColors,
} from '../../normalizeExampleGeojson';

type GeoJsonUploadZoneProps = {
  projectId: string;
  geojsonStatus: 'missing' | 'ready';
  assets: ProjectAssetRead[];
  onRefresh: () => Promise<void>;
  onMapData: (data: FeatureCollection) => void;
  onUploadingChange: (busy: boolean) => void;
};

function checklistLabel(uploaded: boolean): string {
  return uploaded ? 'uploaded' : 'missing';
}

export function GeoJsonUploadZone({
  projectId,
  geojsonStatus,
  assets,
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

  const checklist = geojsonChecklistFromAssets(assets);
  const uploadedCount = (checklist.trenches ? 1 : 0) + (checklist.fcpPolygons ? 1 : 0);

  const applyFile = useCallback(
    async (file: File) => {
      setError(null);
      setSuccessHint(null);

      if (!isAllowedGeoJsonFile(file)) {
        setError('Use a .geojson or .json file.');
        return false;
      }

      const matchedSuffix = requiredGeojsonSuffixForFile(file.name);
      if (!matchedSuffix) {
        setError(
          `Filename must end with ${TRENCHES_GEOJSON_SUFFIX} or ${FCP_POLYGONS_GEOJSON_SUFFIX}.`,
        );
        return false;
      }

      if (file.size > MAX_GEOJSON_BYTES) {
        setError(
          `File is too large (max ${Math.round(MAX_GEOJSON_BYTES / (1024 * 1024))} MB).`,
        );
        return false;
      }

      let parsedFc: FeatureCollection;
      try {
        const text = await file.text();
        const json: unknown = JSON.parse(text);
        parsedFc = stripBlankFillColors(normalizeFeatureCollection(json));
      } catch {
        setError('Could not read valid GeoJSON from this file.');
        return false;
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
        return false;
      }

      onMapData(parsedFc);
      await onRefresh();

      const trenchesAfter =
        checklist.trenches || matchedSuffix === TRENCHES_GEOJSON_SUFFIX;
      const fcpAfter =
        checklist.fcpPolygons || matchedSuffix === FCP_POLYGONS_GEOJSON_SUFFIX;
      const countAfter = (trenchesAfter ? 1 : 0) + (fcpAfter ? 1 : 0);
      const suffixShort =
        matchedSuffix === TRENCHES_GEOJSON_SUFFIX ? 'Trenches' : 'FCP polygons';

      setSuccessHint(
        `${suffixShort} uploaded (${segmentCount} feature${segmentCount === 1 ? '' : 's'}) — ${countAfter} of 2 required files.`,
      );
      return true;
    },
    [projectId, onRefresh, onMapData, onUploadingChange, checklist],
  );

  const applyFiles = useCallback(
    async (files: FileList | File[]) => {
      for (const file of Array.from(files)) {
        const ok = await applyFile(file);
        if (!ok) break;
      }
    },
    [applyFile],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (e.dataTransfer.files.length) {
        void applyFiles(e.dataTransfer.files);
      }
    },
    [applyFiles],
  );

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">GeoJSON route</h3>
      <p className="mt-1 text-xs text-slate-500">
        Upload two files: one ending with <strong>{TRENCHES_GEOJSON_SUFFIX}</strong> and one
        with <strong>{FCP_POLYGONS_GEOJSON_SUFFIX}</strong>. Max{' '}
        {Math.round(MAX_GEOJSON_BYTES / (1024 * 1024))} MB each. Validated on the server.
      </p>

      <ul className="mt-3 space-y-1 text-xs">
        <li className={checklist.trenches ? 'text-emerald-700' : 'text-amber-900'}>
          {checklist.trenches ? '✓' : '○'} {TRENCHES_GEOJSON_SUFFIX} —{' '}
          {checklistLabel(checklist.trenches)}
        </li>
        <li className={checklist.fcpPolygons ? 'text-emerald-700' : 'text-amber-900'}>
          {checklist.fcpPolygons ? '✓' : '○'} {FCP_POLYGONS_GEOJSON_SUFFIX} —{' '}
          {checklistLabel(checklist.fcpPolygons)}
        </li>
      </ul>

      {geojsonStatus === 'missing' && (
        <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-950" role="status">
          <strong className="font-medium">Required GeoJSON files are incomplete.</strong>{' '}
          {uploadedCount === 1
            ? 'Upload the remaining file to enable the route map.'
            : 'The map view cannot be generated until both files are added.'}
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
          multiple
          className="hidden"
          disabled={uploading}
          onChange={(e) => {
            const fl = e.target.files;
            e.target.value = '';
            if (fl?.length) void applyFiles(fl);
          }}
        />
        <span className="text-sm font-medium text-slate-700">
          Drop GeoJSON files here or click to browse
        </span>
        <span className="mt-1 text-xs text-slate-500">
          {uploading ? 'Uploading…' : 'Select one or both required files'}
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
