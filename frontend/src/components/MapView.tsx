import Map from 'react-map-gl/maplibre';

import 'maplibre-gl/dist/maplibre-gl.css';

const DEFAULT_STYLE =
  'https://tiles.openfreemap.org/styles/liberty' as const;

const AUSTRIA_VIEW = {
  longitude: 14.2,
  latitude: 47.6,
  zoom: 6.8,
} as const;

export type MapViewProps = {
  className?: string;
  height?: number;
  longitude?: number;
  latitude?: number;
  zoom?: number;
};

export function MapView({
  className,
  height = 500,
  longitude = AUSTRIA_VIEW.longitude,
  latitude = AUSTRIA_VIEW.latitude,
  zoom = AUSTRIA_VIEW.zoom,
}: MapViewProps) {
  return (
    <div className={className}>
      <Map
        initialViewState={{
          longitude,
          latitude,
          zoom,
        }}
        style={{ width: '100%', height }}
        mapStyle={DEFAULT_STYLE}
      />
    </div>
  );
}
