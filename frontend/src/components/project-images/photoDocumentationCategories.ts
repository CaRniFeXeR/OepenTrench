import type { PhotoDocumentationCategory } from '../../api/client';
import { CATEGORY_COLORS } from '../project-map/photoMarkerPaint';

export type PhotoDocCategoryConfig = {
  id: PhotoDocumentationCategory;
  label: string;
  countKey: 'green' | 'yellow' | 'red';
  color: string;
  filterLabel: string;
  banner: {
    ringClass: string;
    bgClass: string;
    textClass: string;
  };
};

export const PHOTO_DOC_CATEGORIES: PhotoDocCategoryConfig[] = [
  {
    id: 'green',
    label: 'Good',
    countKey: 'green',
    color: CATEGORY_COLORS.green,
    filterLabel: 'good',
    banner: {
      ringClass: 'ring-emerald-500',
      bgClass: 'bg-emerald-50 hover:bg-emerald-100/80',
      textClass: 'text-emerald-900',
    },
  },
  {
    id: 'yellow',
    label: 'Warning',
    countKey: 'yellow',
    color: CATEGORY_COLORS.yellow,
    filterLabel: 'warning',
    banner: {
      ringClass: 'ring-orange-500',
      bgClass: 'bg-orange-50 hover:bg-orange-100/80',
      textClass: 'text-orange-900',
    },
  },
  {
    id: 'red',
    label: 'Failed',
    countKey: 'red',
    color: CATEGORY_COLORS.red,
    filterLabel: 'failed',
    banner: {
      ringClass: 'ring-red-500',
      bgClass: 'bg-red-50 hover:bg-red-100/80',
      textClass: 'text-red-900',
    },
  },
];

export const PHOTO_DOC_CATEGORY_LABELS: Record<PhotoDocumentationCategory, string> = {
  green: PHOTO_DOC_CATEGORIES[0].label,
  yellow: PHOTO_DOC_CATEGORIES[1].label,
  red: PHOTO_DOC_CATEGORIES[2].label,
};

export function photoDocCategoryLabel(id: PhotoDocumentationCategory): string {
  return PHOTO_DOC_CATEGORY_LABELS[id];
}

export function photoDocCategoryFilterLabel(id: PhotoDocumentationCategory): string {
  return PHOTO_DOC_CATEGORIES.find((c) => c.id === id)?.filterLabel ?? id;
}
