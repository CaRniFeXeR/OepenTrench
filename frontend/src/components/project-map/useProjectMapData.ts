import { useEffect, useState } from 'react';

import {
  readProjectMapPhotosProjectsProjectIdMapPhotosGet,
  type MapPhotoMarkerRead,
} from '../../api/client';

export function useProjectMapData(
  projectId: string,
  photoCount: number,
  refreshKey = 0,
) {
  const [mapPhotos, setMapPhotos] = useState<MapPhotoMarkerRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    void (async () => {
      const { data, error: apiError } =
        await readProjectMapPhotosProjectsProjectIdMapPhotosGet({
          path: { project_id: projectId },
        });
      if (cancelled) return;
      setLoading(false);
      if (apiError || !data) {
        setError('Could not load map photos.');
        setMapPhotos([]);
        return;
      }
      setMapPhotos(data.photos);
    })();

    return () => {
      cancelled = true;
    };
  }, [projectId, photoCount, refreshKey]);

  return { mapPhotos, loading, error };
}
