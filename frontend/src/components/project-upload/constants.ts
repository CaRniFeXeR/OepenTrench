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
