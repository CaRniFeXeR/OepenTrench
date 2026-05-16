import { useCallback, useEffect, useState } from 'react';

import {
  listDisagreementsOnlineLearningDisagreementsGet,
  type OnlineLearningDisagreementsPage,
  type OnlineLearningStatsRead,
} from '../../api/client';

export type OnlineLearningPageSize = 25 | 50 | 100;

export function useOnlineLearningDisagreements() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<OnlineLearningPageSize>(25);
  const [data, setData] = useState<OnlineLearningDisagreementsPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const offset = (page - 1) * pageSize;
    const { data: response, error: apiError } =
      await listDisagreementsOnlineLearningDisagreementsGet({
        query: { limit: pageSize, offset },
      });
    setLoading(false);
    if (apiError) {
      setError('Failed to load disagreement photos. Is the API running?');
      setData(null);
      return;
    }
    setData(response ?? null);
  }, [page, pageSize]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setPage(1);
  }, [pageSize]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;
  const startIndex = data && data.total > 0 ? data.offset + 1 : 0;
  const endIndex = data ? Math.min(data.offset + data.items.length, data.total) : 0;

  return {
    items: data?.items ?? [],
    stats: data?.stats ?? null,
    total: data?.total ?? 0,
    loading,
    error,
    page,
    setPage,
    pageSize,
    setPageSize,
    totalPages,
    startIndex,
    endIndex,
    refresh: load,
  };
}

export function emptyStats(): OnlineLearningStatsRead {
  return {
    total_reviewed: 0,
    total_mismatch: 0,
    mismatch_rate: 0,
    projects_with_mismatch: 0,
  };
}
