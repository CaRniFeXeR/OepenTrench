import { useEffect, useState } from 'react';

import {
  calculateProjectFcpCoverageProjectsProjectIdFcpCoveragePost,
  type FcpCoverageRead,
} from '../../api/client';

export function useFcpCoverage(
  projectId: string,
  fcpId: string | null,
  enabled: boolean,
  refreshKey = 0,
) {
  const [coverage, setCoverage] = useState<FcpCoverageRead | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || fcpId === null) {
      setCoverage(null);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    void (async () => {
      const { data, error: apiError } =
        await calculateProjectFcpCoverageProjectsProjectIdFcpCoveragePost({
          path: { project_id: projectId },
          query: { fcp_id: fcpId },
        });
      if (cancelled) return;
      setLoading(false);
      if (apiError || !data) {
        setError('Could not calculate trench coverage.');
        setCoverage(null);
        return;
      }
      setCoverage(data);
    })();

    return () => {
      cancelled = true;
    };
  }, [projectId, fcpId, enabled, refreshKey]);

  return { coverage, loading, error };
}
