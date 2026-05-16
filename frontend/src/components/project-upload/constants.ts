/** Mirrors backend [src/api/services/project_asset_service.py] and [src/api/uploads.py]. */
export const MAX_IMAGE_BYTES = 50 * 1024 * 1024;
export const MAX_GEOJSON_BYTES = 10 * 1024 * 1024;
export const MAX_PHOTOS_PER_BATCH = 1000;

/** Allowed image suffixes on the server (no HEIC). */
export const IMAGE_EXTENSIONS = new Set([
  '.jpg',
  '.jpeg',
  '.png',
  '.webp',
  '.gif',
]);

export const IMAGE_ACCEPT =
  'image/jpeg,image/png,image/webp,image/gif,.jpg,.jpeg,.png,.webp,.gif';

export const GEOJSON_ACCEPT = '.geojson,.json,application/geo+json,application/json';

export function fileExtensionLower(name: string): string {
  const i = name.lastIndexOf('.');
  if (i < 0) return '';
  return name.slice(i).toLowerCase();
}

export function isAllowedImageFile(file: File): boolean {
  return IMAGE_EXTENSIONS.has(fileExtensionLower(file.name));
}

export function isAllowedGeoJsonFile(file: File): boolean {
  const ext = fileExtensionLower(file.name);
  return ext === '.geojson' || ext === '.json';
}

export const TRENCHES_GEOJSON_SUFFIX = 'Trenches.geojson';
export const FCP_POLYGONS_GEOJSON_SUFFIX = 'FCP_Polygons.geojson';

export function endswithGeojsonSuffix(name: string, suffix: string): boolean {
  return name.trim().toLowerCase().endsWith(suffix.toLowerCase());
}

export function requiredGeojsonSuffixForFile(name: string): string | null {
  if (endswithGeojsonSuffix(name, TRENCHES_GEOJSON_SUFFIX)) {
    return TRENCHES_GEOJSON_SUFFIX;
  }
  if (endswithGeojsonSuffix(name, FCP_POLYGONS_GEOJSON_SUFFIX)) {
    return FCP_POLYGONS_GEOJSON_SUFFIX;
  }
  return null;
}

export function geojsonChecklistFromAssets(
  assets: { kind: string; original_label: string }[],
): { trenches: boolean; fcpPolygons: boolean } {
  const geo = assets.filter((a) => a.kind === 'geojson');
  return {
    trenches: geo.some((a) => endswithGeojsonSuffix(a.original_label, TRENCHES_GEOJSON_SUFFIX)),
    fcpPolygons: geo.some((a) =>
      endswithGeojsonSuffix(a.original_label, FCP_POLYGONS_GEOJSON_SUFFIX),
    ),
  };
}
