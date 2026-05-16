import {
  forwardRef,
  type ForwardedRef,
  type ReactNode,
} from 'react';

import Map, { type MapRef } from 'react-map-gl/maplibre';
import type {
  LngLatBoundsLike,
  MapLayerMouseEvent,
  MapLibreEvent,
  PaddingOptions,
} from 'maplibre-gl';

import 'maplibre-gl/dist/maplibre-gl.css';

const DEFAULT_STYLE =
  'https://tiles.openfreemap.org/styles/liberty' as const;

const AUSTRIA_VIEW = {
  longitude: 14.2,
  latitude: 47.6,
  zoom: 6.8,
} as const;

export type MapFitBoundsOptions = {
  offset?: [number, number];
  minZoom?: number;
  maxZoom?: number;
  padding?: number | PaddingOptions;
};

export type MapViewProps = {
  className?: string;
  height?: number;
  longitude?: number;
  latitude?: number;
  zoom?: number;
  bounds?: LngLatBoundsLike;
  fitBoundsOptions?: MapFitBoundsOptions;
  onLoad?: (e: MapLibreEvent) => void;
  onClick?: (e: MapLayerMouseEvent) => void;
  interactiveLayerIds?: string[];
  children?: ReactNode;
};

export const MapView = forwardRef(function MapView(
  {
    className,
    height = 500,
    longitude = AUSTRIA_VIEW.longitude,
    latitude = AUSTRIA_VIEW.latitude,
    zoom = AUSTRIA_VIEW.zoom,
    bounds,
    fitBoundsOptions,
    onLoad,
    onClick,
    interactiveLayerIds,
    children,
  }: MapViewProps,
  ref: ForwardedRef<MapRef | null>,
) {
  const initialViewState = bounds
    ? { bounds, fitBoundsOptions }
    : { longitude, latitude, zoom };

  return (
    <div className={className}>
      <Map
        ref={ref}
        initialViewState={initialViewState}
        style={{ width: '100%', height }}
        mapStyle={DEFAULT_STYLE}
        onLoad={onLoad}
        onClick={onClick}
        interactiveLayerIds={interactiveLayerIds}
      >
        {children}
      </Map>
    </div>
  );
});
