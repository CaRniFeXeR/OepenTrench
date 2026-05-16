import type { ProjectAssetRead } from '../../api/client';
import { missingGeojsonMessage } from './routeStatus';

export function RouteUploadStatus({
  routeReady,
  uploadsBusy,
  assets,
  variant = 'inline',
}: {
  routeReady: boolean;
  uploadsBusy: boolean;
  assets: ProjectAssetRead[];
  variant?: 'inline' | 'footer';
}) {
  const statusMessage = missingGeojsonMessage(routeReady, assets);

  if (routeReady && !uploadsBusy) {
    return (
      <span
        className={`font-medium text-emerald-700 ${
          variant === 'footer' ? '' : 'text-xs'
        }`}
      >
        {variant === 'footer' ? 'Route files ready ✓' : 'Route ready ✓'}
      </span>
    );
  }

  if (uploadsBusy) {
    return (
      <span className={variant === 'footer' ? '' : 'text-xs text-slate-600'}>
        Upload in progress…
      </span>
    );
  }

  if (!statusMessage) return null;

  return (
    <span
      className={`font-medium text-amber-800 ${
        variant === 'inline' ? 'max-w-xs text-xs' : ''
      }`}
    >
      {statusMessage}
    </span>
  );
}
