import { Layer, Source } from 'react-map-gl/maplibre';
import type { FeatureCollection } from 'geojson';
import type {
  FillLayerSpecification,
  FilterSpecification,
  LineLayerSpecification,
} from '@maplibre/maplibre-gl-style-spec';

import { photoCircleLayout, photoCirclePaint } from './photoMarkerPaint';

export const LAYER_FCP_FILL = 'project-fcp-fill';
export const LAYER_FCP_OUTLINE = 'project-fcp-outline';
export const LAYER_TRENCHES = 'project-trenches-line';
export const LAYER_COVERAGE = 'project-coverage-compartments-line';
export const LAYER_PHOTOS = 'project-photos-circle';

const FILTER_POLYGON: FilterSpecification = [
  'any',
  ['==', ['geometry-type'], 'Polygon'],
  ['==', ['geometry-type'], 'MultiPolygon'],
];

const FILTER_LINE: FilterSpecification = [
  'any',
  ['==', ['geometry-type'], 'LineString'],
  ['==', ['geometry-type'], 'MultiLineString'],
];

const trenchPaint = {
  'line-color': '#64748b',
  'line-width': 2,
} as NonNullable<LineLayerSpecification['paint']>;

const coveragePaint = {
  'line-color': [
    'case',
    ['==', ['get', 'covered'], true],
    '#22c55e',
    '#ef4444',
  ],
  'line-width': 5,
} as NonNullable<LineLayerSpecification['paint']>;

const fcpFillPaint = {
  'fill-color': '#7c3aed',
  'fill-opacity': [
    'case',
    ['==', ['get', 'selected'], true],
    0.35,
    ['==', ['get', 'deemphasized'], true],
    0.08,
    0.2,
  ],
} as NonNullable<FillLayerSpecification['paint']>;

const fcpOutlinePaint = {
  'line-color': [
    'case',
    ['==', ['get', 'selected'], true],
    '#5b21b6',
    '#a78bfa',
  ],
  'line-width': [
    'case',
    ['==', ['get', 'selected'], true],
    3,
    1.5,
  ],
} as NonNullable<LineLayerSpecification['paint']>;

export function ProjectMapLayers({
  trenches,
  fcpPolygons,
  photoMarkers,
  coverageCompartments,
  selectedFcpId,
}: {
  trenches: FeatureCollection;
  fcpPolygons: FeatureCollection;
  photoMarkers: FeatureCollection;
  coverageCompartments?: FeatureCollection | null;
  selectedFcpId: string | null;
}) {
  const fcpWithSelection: FeatureCollection = {
    type: 'FeatureCollection',
    features: fcpPolygons.features.map((feature) => {
      const props = (feature.properties ?? {}) as Record<string, unknown>;
      const fcpId = props.fcp_id != null ? String(props.fcp_id) : null;
      const selected = selectedFcpId != null && fcpId === selectedFcpId;
      const deemphasized =
        selectedFcpId != null && fcpId != null && fcpId !== selectedFcpId;
      return {
        ...feature,
        properties: {
          ...props,
          selected,
          deemphasized,
        },
      };
    }),
  };

  return (
    <>
      <Source id="project-trenches" type="geojson" data={trenches}>
        <Layer
          id={LAYER_TRENCHES}
          type="line"
          paint={trenchPaint}
          filter={FILTER_LINE}
        />
      </Source>
      {coverageCompartments && coverageCompartments.features.length > 0 && (
        <Source id="project-coverage" type="geojson" data={coverageCompartments}>
          <Layer
            id={LAYER_COVERAGE}
            type="line"
            paint={coveragePaint}
            filter={FILTER_LINE}
          />
        </Source>
      )}
      <Source id="project-fcp" type="geojson" data={fcpWithSelection}>
        <Layer
          id={LAYER_FCP_FILL}
          type="fill"
          paint={fcpFillPaint}
          filter={FILTER_POLYGON}
        />
        <Layer
          id={LAYER_FCP_OUTLINE}
          type="line"
          paint={fcpOutlinePaint}
          filter={FILTER_POLYGON}
        />
      </Source>
      <Source id="project-photos" type="geojson" data={photoMarkers}>
        <Layer
          id={LAYER_PHOTOS}
          type="circle"
          layout={photoCircleLayout}
          paint={photoCirclePaint}
        />
      </Source>
    </>
  );
}
