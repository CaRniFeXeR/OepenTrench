import type { ProjectAssetRead } from '../../api/client';
import {
  FCP_POLYGONS_GEOJSON_SUFFIX,
  TRENCHES_GEOJSON_SUFFIX,
  geojsonChecklistFromAssets,
} from '../project-upload/constants';

export function missingGeojsonMessage(
  routeReady: boolean,
  assets: ProjectAssetRead[],
): string {
  if (routeReady) return '';
  const checklist = geojsonChecklistFromAssets(assets);
  const missing: string[] = [];
  if (!checklist.trenches) missing.push(TRENCHES_GEOJSON_SUFFIX);
  if (!checklist.fcpPolygons) missing.push(FCP_POLYGONS_GEOJSON_SUFFIX);
  if (missing.length === 2) {
    return 'Missing GeoJSON — upload Trenches and FCP_Polygons route files ⚠';
  }
  return `Still needed: ${missing.join(', ')} ⚠`;
}
