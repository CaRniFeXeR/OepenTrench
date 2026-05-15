const geojsonUrls = import.meta.glob<string>(
  '../../data/example_geojson/*.geojson',
  { eager: true, import: 'default', query: '?url' },
);

function fileLabelFromModulePath(modulePath: string): string {
  const segment = modulePath.split('/').pop() ?? modulePath;
  return segment.replace(/\.geojson$/i, '') || modulePath;
}

/** MapLibre source and layer ids allow [a-zA-Z0-9-_]. */
export function sanitizeMapId(raw: string): string {
  return raw.replace(/[^a-zA-Z0-9_-]/g, '_');
}

export type ExampleGeojsonDataset = {
  /** Sanitized id for MapLibre Source `id` */
  id: string;
  /** Human-readable name (filename without extension) */
  label: string;
  /** Asset URL from Vite */
  url: string;
};

export const EXAMPLE_GEOJSON_DATASETS: ExampleGeojsonDataset[] = Object.entries(
  geojsonUrls,
)
  .map(([modulePath, url]) => {
    const label = fileLabelFromModulePath(modulePath);
    return {
      id: sanitizeMapId(label),
      label,
      url,
    };
  })
  .sort((a, b) => a.label.localeCompare(b.label));
