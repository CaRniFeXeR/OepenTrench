import exifr from 'exifr';

/**
 * Returns whether the image has usable GPS coordinates in EXIF (best-effort).
 */
export async function fileHasExifGps(file: File): Promise<boolean> {
  try {
    const gps = await exifr.gps(file);
    if (!gps || typeof gps !== 'object') return false;
    const lat = (gps as { latitude?: unknown }).latitude;
    const lon = (gps as { longitude?: unknown }).longitude;
    return typeof lat === 'number' && typeof lon === 'number';
  } catch {
    return false;
  }
}
