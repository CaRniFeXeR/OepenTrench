import { Layer, Source } from 'react-map-gl/maplibre';
import type { FeatureCollection } from 'geojson';
import type {
  CircleLayerSpecification,
  FillLayerSpecification,
  FilterSpecification,
  LineLayerSpecification,
} from '@maplibre/maplibre-gl-style-spec';

const ROUTE_BLUE = '#3b82f6';

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

const FILTER_POINT: FilterSpecification = [
  '==',
  ['geometry-type'],
  'Point',
];

const fillPaint = {
  'fill-color': ROUTE_BLUE,
  'fill-opacity': 0.25,
} as NonNullable<FillLayerSpecification['paint']>;

const polygonOutlinePaint = {
  'line-color': ROUTE_BLUE,
  'line-width': 2,
} as NonNullable<LineLayerSpecification['paint']>;

const linePaint = {
  'line-color': ROUTE_BLUE,
  'line-width': 3,
} as NonNullable<LineLayerSpecification['paint']>;

const circlePaint = {
  'circle-radius': 5,
  'circle-color': ROUTE_BLUE,
  'circle-stroke-width': 1,
  'circle-stroke-color': '#1e293b',
} as NonNullable<CircleLayerSpecification['paint']>;

export function GeoJsonRouteLayers({
  data,
  sourceId,
}: {
  data: FeatureCollection;
  sourceId: string;
}) {
  return (
    <Source id={sourceId} type="geojson" data={data}>
      <Layer
        id={`${sourceId}-fill`}
        type="fill"
        paint={fillPaint}
        filter={FILTER_POLYGON}
      />
      <Layer
        id={`${sourceId}-poly-line`}
        type="line"
        paint={polygonOutlinePaint}
        filter={FILTER_POLYGON}
      />
      <Layer
        id={`${sourceId}-line`}
        type="line"
        paint={linePaint}
        filter={FILTER_LINE}
      />
      <Layer
        id={`${sourceId}-circle`}
        type="circle"
        paint={circlePaint}
        filter={FILTER_POINT}
      />
    </Source>
  );
}
