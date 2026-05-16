import type { ProjectAssetRead } from '../../api/client';
import { effectiveCategory } from '../project-map/mapPhotoUtils';

export type QualityFilter = 'all' | 'good' | 'poor' | 'missing' | 'pending';
export type ImageSortOption = 'newest' | 'name_asc' | 'name_desc';
export type PageSize = 25 | 50 | 100;

export type ImageQualityBucket = 'good' | 'poor' | 'missing' | 'pending';

export function imageAssets(assets: ProjectAssetRead[]): ProjectAssetRead[] {
  return assets.filter((a) => a.kind === 'image');
}

export function imageQualityBucket(asset: ProjectAssetRead): ImageQualityBucket {
  if (!asset.analysis) {
    return 'pending';
  }
  const cat = effectiveCategory(
    asset.analysis.reviewer_override_category ?? asset.analysis.category ?? null,
  );
  if (cat === 'green') return 'good';
  if (cat === 'yellow') return 'poor';
  return 'missing';
}

export function filterImages(
  images: ProjectAssetRead[],
  qualityFilter: QualityFilter,
  searchQuery: string,
): ProjectAssetRead[] {
  const q = searchQuery.trim().toLowerCase();
  return images.filter((asset) => {
    if (qualityFilter !== 'all' && imageQualityBucket(asset) !== qualityFilter) {
      return false;
    }
    if (!q) {
      return true;
    }
    return asset.original_label.toLowerCase().includes(q);
  });
}

export function sortImages(
  images: ProjectAssetRead[],
  sort: ImageSortOption,
): ProjectAssetRead[] {
  const copy = [...images];
  if (sort === 'name_asc') {
    copy.sort((a, b) =>
      a.original_label.localeCompare(b.original_label, undefined, { sensitivity: 'base' }),
    );
  } else if (sort === 'name_desc') {
    copy.sort((a, b) =>
      b.original_label.localeCompare(a.original_label, undefined, { sensitivity: 'base' }),
    );
  } else {
    copy.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
  }
  return copy;
}

export function paginateImages<T>(
  items: T[],
  page: number,
  pageSize: PageSize,
): { pageItems: T[]; totalPages: number; startIndex: number; endIndex: number } {
  const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const startIndex = (safePage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, items.length);
  return {
    pageItems: items.slice(startIndex, endIndex),
    totalPages,
    startIndex,
    endIndex,
  };
}

export function formatAssetDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString();
}
