import { useCallback, useEffect, useRef, useState } from 'react';

import {
  listTrainingsOnlineLearningTrainingsGet,
  startTrainingOnlineLearningTrainingsPost,
  type OnlineLearningTrainingRunRead,
} from '../../api/client';

const POLL_MS = 3000;

export function useOnlineLearningTrainings() {
  const [trainings, setTrainings] = useState<OnlineLearningTrainingRunRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    const { data: response, error: apiError } = await listTrainingsOnlineLearningTrainingsGet({
      query: { limit: 50, offset: 0 },
    });
    if (apiError) {
      setError('Failed to load training runs. Is the API running?');
      return false;
    }
    setError(null);
    setTrainings(response?.items ?? []);
    return true;
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    await load();
    setLoading(false);
  }, [load]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const isTraining = trainings.some((t) => t.status === 'running');

  useEffect(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    if (!isTraining) {
      return;
    }
    pollRef.current = setInterval(() => {
      void load();
    }, POLL_MS);
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [isTraining, load]);

  const startTraining = useCallback(async () => {
    setStartError(null);
    const { data: run, error: apiError, response } =
      await startTrainingOnlineLearningTrainingsPost();
    if (apiError) {
      if (response?.status === 409) {
        setStartError('A training run is already in progress.');
      } else {
        setStartError('Failed to start training. Is the API running?');
      }
      return false;
    }
    if (run) {
      setTrainings((prev) => {
        const rest = prev.filter((t) => t.id !== run.id);
        return [run, ...rest];
      });
    }
    void load();
    return true;
  }, [load]);

  return {
    trainings,
    loading,
    error,
    startError,
    isTraining,
    startTraining,
    refresh,
  };
}
