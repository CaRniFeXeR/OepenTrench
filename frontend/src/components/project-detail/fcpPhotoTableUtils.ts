import type { FeatureCollection } from 'geojson';

import type { MapPhotoMarkerRead, ProjectAssetRead } from '../../api/client';
import {
  analysisEffectiveCategory,
  UNASSOCIATED_FCP_ID,
  isUnassociatedFcpId,
} from '../project-images/photoDocumentationUtils';

export { UNASSOCIATED_FCP_ID, isUnassociatedFcpId };
import {
  fcpCodeFromProperties,
  fcpIdFromProperties,
  fcpLabelFromProperties,
} from '../project-map/fcpFromProperties';
import { enrichFcpPolygons, splitProjectGeojson } from '../project-map/splitProjectGeojson';

export type FcpPhotoRow = {
  fcpId: string;
  fcpCode: string;
  fcpLabel: string;
  green: number;
  yellow: number;
  red: number;
};

export function assetIdToFcpId(
  mapPhotos: MapPhotoMarkerRead[],
): Map<string, string> {
  const map = new Map<string, string>();
  for (const photo of mapPhotos) {
    if (photo.fcp_id) {
      map.set(photo.asset_id, photo.fcp_id);
    }
  }
  return map;
}

export function buildFcpPhotoRows({
  assets,
  mapPhotos,
  mapData,
}: {
  assets: ProjectAssetRead[];
  mapPhotos: MapPhotoMarkerRead[];
  mapData: FeatureCollection | null;
}): FcpPhotoRow[] {
  if (!mapData) return [];

  const { fcpPolygons } = splitProjectGeojson(mapData);
  const enriched = enrichFcpPolygons(fcpPolygons);
  const assetFcpMap = assetIdToFcpId(mapPhotos);

  const rowsById = new Map<string, FcpPhotoRow>();

  for (const feature of enriched.features) {
    const props = (feature.properties ?? {}) as Record<string, unknown>;
    const fcpId = fcpIdFromProperties(props);
    if (!fcpId) continue;
    rowsById.set(fcpId, {
      fcpId,
      fcpCode: fcpCodeFromProperties(props),
      fcpLabel: fcpLabelFromProperties(props),
      green: 0,
      yellow: 0,
      red: 0,
    });
  }

  for (const asset of assets) {
    if (asset.kind !== 'image' || !asset.analysis) continue;
    const fcpId = assetFcpMap.get(asset.id);
    if (!fcpId) continue;

    let row = rowsById.get(fcpId);
    if (!row) {
      const photo = mapPhotos.find((p) => p.fcp_id === fcpId);
      row = {
        fcpId,
        fcpCode: photo?.fcp_code ?? fcpId,
        fcpLabel: photo?.fcp_label ?? fcpId,
        green: 0,
        yellow: 0,
        red: 0,
      };
      rowsById.set(fcpId, row);
    }

    const cat = analysisEffectiveCategory(asset.analysis);
    if (cat === 'green') row.green += 1;
    else if (cat === 'yellow') row.yellow += 1;
    else if (cat === 'red') row.red += 1;
  }

  return [...rowsById.values()].sort((a, b) =>
    a.fcpCode.localeCompare(b.fcpCode, undefined, { sensitivity: 'base' }),
  );
}

export function buildUnassociatedPhotoRow(
  assets: ProjectAssetRead[],
  assetFcpMap: Map<string, string>,
): FcpPhotoRow | null {
  let yellow = 0;
  let red = 0;
  let green = 0;
  let total = 0;

  for (const asset of assets) {
    if (asset.kind !== 'image' || !asset.analysis) continue;
    if (assetFcpMap.has(asset.id)) continue;
    total += 1;
    const cat = analysisEffectiveCategory(asset.analysis);
    if (cat === 'green') green += 1;
    else if (cat === 'yellow') yellow += 1;
    else if (cat === 'red') red += 1;
  }

  if (total === 0) return null;

  return {
    fcpId: UNASSOCIATED_FCP_ID,
    fcpCode: 'No FCP',
    fcpLabel: 'No GPS or not inside an FCP polygon',
    green,
    yellow,
    red,
  };
}

export function fcpCodeForId(
  rows: FcpPhotoRow[],
  fcpId: string | null,
): string | null {
  if (!fcpId) return null;
  if (isUnassociatedFcpId(fcpId)) return 'No FCP';
  return rows.find((r) => r.fcpId === fcpId)?.fcpCode ?? null;
}
