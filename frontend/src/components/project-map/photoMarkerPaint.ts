import type { CircleLayerSpecification } from '@maplibre/maplibre-gl-style-spec';

export const CATEGORY_COLORS = {
  green: '#22c55e',
  yellow: '#f97316',
  red: '#ef4444',
  unknown: '#94a3b8',
} as const;

export const photoCirclePaint = {
  'circle-radius': [
    'case',
    ['boolean', ['get', 'highlighted'], false],
    12,
    7,
  ],
  'circle-color': [
    'match',
    ['get', 'category'],
    'green',
    CATEGORY_COLORS.green,
    'yellow',
    CATEGORY_COLORS.yellow,
    'red',
    CATEGORY_COLORS.red,
    CATEGORY_COLORS.unknown,
  ],
  'circle-stroke-width': [
    'case',
    ['boolean', ['get', 'highlighted'], false],
    3,
    1.5,
  ],
  'circle-stroke-color': [
    'case',
    ['boolean', ['get', 'highlighted'], false],
    '#ffffff',
    '#1e293b',
  ],
  'circle-opacity': [
    'case',
    ['boolean', ['get', 'dimmed'], false],
    0.35,
    1,
  ],
} as NonNullable<CircleLayerSpecification['paint']>;
