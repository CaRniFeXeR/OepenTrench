import { useCallback, useEffect, useState } from 'react';

import {
  readProjectProjectsProjectIdGet,
  type ProjectDetailRead,
} from '../../api/client';

export function useProjectDetail(projectId: string | undefined) {
  const [project, setProject] = useState<ProjectDetailRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadsBusy, setUploadsBusy] = useState(false);

  const load = useCallback(async (options?: { silent?: boolean }) => {
    if (!projectId) {
      setError('Missing project id.');
      setLoading(false);
      return;
    }

    const silent = options?.silent ?? false;
    if (!silent) {
      setLoading(true);
    }
    setError(null);
    const { data, error: apiError } = await readProjectProjectsProjectIdGet({
      path: { project_id: projectId },
    });
    if (!silent) {
      setLoading(false);
    }

    if (apiError) {
      setError('Project not found or failed to load.');
      setProject(null);
      return;
    }

    setProject(data ?? null);
  }, [projectId]);

  const refreshProject = useCallback(async () => {
    await load({ silent: true });
  }, [load]);

  useEffect(() => {
    queueMicrotask(() => {
      void load();
    });
  }, [load]);

  return {
    project,
    loading,
    error,
    uploadsBusy,
    setUploadsBusy,
    refreshProject,
  };
}
