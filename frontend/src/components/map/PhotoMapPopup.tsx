import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useMap } from 'react-map-gl/maplibre';

export function PhotoMapPopup({
  longitude,
  latitude,
  imageUrl,
  title,
  subtitle,
  categoryLabel,
  onClose,
}: {
  longitude: number;
  latitude: number;
  imageUrl: string;
  title: string;
  subtitle?: string;
  categoryLabel?: string;
  onClose: () => void;
}) {
  const { current: mapRef } = useMap();
  const [portalRoot, setPortalRoot] = useState<HTMLElement | null>(null);
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const map = mapRef?.getMap();
    if (!map) return;

    const parent = map.getContainer().parentElement;
    if (!parent) return;
    setPortalRoot(parent);

    const updatePosition = () => {
      const point = map.project([longitude, latitude]);
      setPosition({ x: point.x, y: point.y });
    };

    updatePosition();
    map.on('move', updatePosition);
    map.on('zoom', updatePosition);
    map.on('rotate', updatePosition);
    map.on('pitch', updatePosition);
    map.on('resize', updatePosition);

    return () => {
      map.off('move', updatePosition);
      map.off('zoom', updatePosition);
      map.off('rotate', updatePosition);
      map.off('pitch', updatePosition);
      map.off('resize', updatePosition);
    };
  }, [mapRef, longitude, latitude]);

  if (!portalRoot || !position) return null;

  return createPortal(
    <div className="pointer-events-none absolute inset-0 z-30" role="presentation">
      <div
        className="pointer-events-auto absolute w-[260px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl"
        style={{
          left: position.x,
          top: position.y,
          transform: 'translate(-50%, calc(-100% - 12px))',
        }}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-1.5 top-1.5 z-10 flex h-6 w-6 items-center justify-center rounded-full bg-white/90 text-slate-600 shadow hover:bg-white hover:text-slate-900"
          aria-label="Close photo preview"
        >
          ×
        </button>
        <img
          src={imageUrl}
          alt={title}
          className="max-h-40 w-full bg-slate-100 object-contain"
        />
        <div className="space-y-1 p-2 pr-8">
          <p className="line-clamp-2 text-sm font-medium text-slate-900" title={title}>
            {title}
          </p>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
          {categoryLabel && (
            <span className="inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
              {categoryLabel}
            </span>
          )}
        </div>
      </div>
    </div>,
    portalRoot,
  );
}
