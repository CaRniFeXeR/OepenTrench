import { useCallback, useEffect, useState } from 'react';

import {
  calculateProjectFcpCoverageProjectsProjectIdFcpCoveragePost,
  readProjectFcpCoverageProjectsProjectIdFcpCoverageGet,
  type FcpCoverageRead,
} from '../../api/client';

export function useProjectFcpCoverage(
  projectId: string,
  routeReady: boolean,
  refreshKey = 0,
) {
  const [coverage, setCoverage] = useState<FcpCoverageRead | null>(null);
  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCoverage = useCallback(async () => {
    if (!routeReady) {
      setCoverage(null);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    const { data, error: apiError } =
      await readProjectFcpCoverageProjectsProjectIdFcpCoverageGet({
        path: { project_id: projectId },
      });
    setLoading(false);
    if (apiError || !data) {
      setError('Could not load trench coverage.');
      setCoverage(null);
      return;
    }
    setCoverage(data);
  }, [projectId, routeReady]);

  useEffect(() => {
    void fetchCoverage();
  }, [fetchCoverage, refreshKey]);

  const calculateCoverage = useCallback(async () => {
    if (!routeReady) return;

    setCalculating(true);
    setError(null);
    const { data, error: apiError } =
      await calculateProjectFcpCoverageProjectsProjectIdFcpCoveragePost({
        path: { project_id: projectId },
      });
    setCalculating(false);
    if (apiError || !data) {
      setError('Could not calculate trench coverage.');
      return;
    }
    setCoverage(data);
  }, [projectId, routeReady]);

  return {
    coverage,
    loading,
    calculating,
    error,
    calculateCoverage,
    refresh: fetchCoverage,
  };
}
